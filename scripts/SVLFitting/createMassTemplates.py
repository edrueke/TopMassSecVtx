#!/usr/bin/env python

import ROOT
import os,sys
import optparse

"""
parses files with histograms and converts them to RooFit objects
in a common workspace
"""

# MASSES = [163.5, 166.5, 169.5, 172.5, 173.5, 175.5, 178.5, 181.5]
MASSES = [166.5, 169.5, 172.5, 173.5, 175.5, 178.5]

def checkKeyInFile(key, filehandle, doraise=True):
    obj = ROOT.TObject()
    try:
        filehandle.GetObject(key, obj)
        return True
    except LookupError, e:
        print ("Error: key %s not found in file %s" %
                  (key, filehandle.GetName()))
        if doraise:
            raise e
        else:
            return False


def createWorkspace(sigFile, selection, outdir):
"""
    Create the RooFit workspace with the data and fit model and do the fits
"""
    # Initiate a workspace where the observable is M_{bl}
    # and the variable to fit is M_{t}
    ws = ROOT.RooWorkspace('w')
    ws.factory('mtop[172.5,100,200]')
    ws.factory('mbl[100,0,300]')
    mbl = ws.var('mbl')

    #import signal PDFs from files
    correctH = {}
    totalWrongH = None
    sig_mass_cats = 'sig_mass_cats['
    fIn = ROOT.TFile.Open(sigFile)
    for mass in MASSES:
        iCat = str(mass).replace('.','')
        sig_mass_cats += 'm%s=%3.1f,'%(iCat,mass)

        # Correct assignments are imported separately
        histn = 'SVLMass_%s_%s_%s'%('cor',selection,str(mass).replace('.', ''))
        if checkKeyInFile(histn, fIn):
            correctH[iCat] = fIn.Get(histn).Clone()
            correctH[iCat].SetDirectory(0)
            correctH[iCat].SetTitle('[%3.1f GeV]' % mass)

        # Wrong assignments are added up to increase statistics
        histn = 'SVLMass_%s_%s_%s'%('wro',selection,str(mass).replace('.', ''))
        if checkKeyInFile(histn, fIn):
            if totalWrongH is None:
                totalWrongH = fIn.Get(histn).Clone('wro')
                totalWrongH.SetDirectory(0)
            else :
                totalWrongH.Add(fIn.Get(histn))
    fIn.Close()

    getattr(ws,'import')(ROOT.RooDataHist('wrong','Wrong assignments',
                                           ROOT.RooArgList(mbl),
                                           totalWrongH))

    # Perform a combined parameterization of the signal:
    # ~ f.gaussian+(1-f).gamma
    # Where all parameters are assumed to be linear functions of
    # the top quark mass

    # Fraction
    ws.factory("RooFormulaVar::sig_frac('@0*(@1-172.5)+@2',{"
                  "a_sig_frac[0.,-2.0,2.0],"
                  "mtop,"
                  "b_sig_frac[0.90,0.0,1]})")


    # Asymmetric gaussian parameters
    ws.factory("RooFormulaVar::sig_agauss_mean('@0*(@1-172.5)+@2',{"
                "a_sig_agauss_mean[0.01,-1,2],"
                "mtop,"
                "b_sig_agauss_mean[50,0,100]})")
    ws.factory("RooFormulaVar::sig_agauss_sigmaL('@0*(@1-172.5)+@2',{"
                "a_sig_agauss_sigmaL[0.01,-1,2],"
                "mtop,"
                "b_sig_agauss_sigmaL[15,-100,100]})")
    ws.factory("RooFormulaVar::sig_agauss_sigmaR('@0*(@1-172.5)+@2',{"
                "a_sig_agauss_sigmaR[0.01,-1,2],"
                "mtop,"
                "b_sig_agauss_sigmaR[25,-100,100]})")

    # Non gaussian function parameters
    ws.factory("RooFormulaVar::sig_ngauss_gamma('@0*(@1-172.5)+@2',{"
               "a_sig_ngauss_gamma[0,-1,1],"
               "mtop,"
               "b_sig_ngauss_gamma[8,0.1,10]})")
    ws.factory("RooFormulaVar::sig_ngauss_beta('@0*(@1-172.5)+@2',{"
               "a_sig_ngauss_beta[0,-1,1],"
               "mtop,"
               "b_sig_ngauss_beta[10,0.1,20]})")
    ws.factory("RooFormulaVar::sig_ngauss_mu('@0*(@1-172.5)+@2',{"
               "a_sig_ngauss_mu[0,-2,2],"
               "mtop,"
               "b_sig_ngauss_mu[0,-5,5]})")

    # ws.factory("RooFormulaVar::sig_ngauss_gamma(' @0*( @1-172.5)+ @2' , {a_sig_ngauss_gamma[0,-1,1], mtop , b_sig_ngauss_gamma[40 , 0   , 200]})")
    # ws.factory("RooFormulaVar::sig_ngauss_beta( ' @0*( @1-172.5)+ @2' , {a_sig_ngauss_beta[0,-1,1],  mtop , b_sig_ngauss_beta[-20 , -50 , 50]})")

    # ws.factory("RooFormulaVar::sig_ngauss_gamma(' @0*( @1-172.5)+ @2' , {a_sig_ngauss_gamma[0] ,     mtop , b_sig_ngauss_gamma[0 , -1   , 1]})")
    # ws.factory("RooFormulaVar::sig_ngauss_beta('  @0*( @1-172.5)+ @2' , {a_sig_ngauss_beta[0]  ,     mtop , b_sig_ngauss_beta[0  , -1   , 1]})")
    # ws.factory("RooFormulaVar::sig_ngauss_mu('    @0*( @1-172.5)+ @2' , {a_sig_ngauss_mu[0]    ,     mtop , b_sig_ngauss_mu[0    , -1   , 1]})")
    # ws.factory("RooFormulaVar::sig_ngauss_nu('    @0*( @1-172.5)+ @2' , {a_sig_ngauss_nu[0]    ,     mtop , b_sig_ngauss_nu[0    , -1   , 1]})")
    # ws.factory("RooFormulaVar::sig_ngauss_kappa(' @0*( @1-172.5)+ @2' , {a_sig_ngauss_kappa[0] ,     mtop , b_sig_ngauss_kappa[0 , -1   , 1]})")



    # The base signal PDF
    ws.factory("SUM::sigmodel("
               "sig_frac*RooBifurGauss::sig_agauss("
                 "mbl,sig_agauss_mean,sig_agauss_sigmaL,sig_agauss_sigmaR),"
               "RooGamma::sig_ngauss("
                 "mbl,sig_ngauss_gamma,sig_ngauss_beta,sig_ngauss_mu))")
    # ws.factory("SUM::sigmodel("
    #            "sig_frac*RooBifurGauss::sig_agauss("
    #              "mbl,sig_agauss_mean,sig_agauss_sigmaL,sig_agauss_sigmaR),"
    #            "RooGaussian::sig_ngauss("
    #              "mbl,sig_ngauss_gamma,sig_ngauss_beta))")
    # ws.factory("SUM::sigmodel("
    #            "sig_frac*RooBifurGauss::sig_agauss("
    #              "mbl,sig_agauss_mean,sig_agauss_sigmaL,sig_agauss_sigmaR),"
    #            "RooArgusBG::sig_ngauss("
    #              "mbl,sig_ngauss_gamma,sig_ngauss_beta))")
    # ws.factory("SUM::sigmodel("
    #            "sig_frac*RooBifurGauss::sig_agauss("
    #              "mbl,sig_agauss_mean,sig_agauss_sigmaL,sig_agauss_sigmaR),"
    #            "RooChebychev::sig_ngauss("
    #              "mbl,{sig_ngauss_gamma,sig_ngauss_beta,sig_ngauss_mu,"
    #                    "sig_ngauss_nu,sig_ngauss_kappa}))")





    # The PDF to be fit simultaneously to all signals:
    # mtop is specialized in each category
    sig_mass_cats = sig_mass_cats[:-1]+']'
    ## sig_mass_cats[m1615=161.5,m1685=168.5...]
    ws.factory("SIMCLONE::sigmodel_sim( sigmodel, $SplitParam({mtop},%s))"
                  % sig_mass_cats)
    for mass in MASSES:
        iCat = str(mass).replace('.','')
        ws.var('mtop_m%s'%iCat).setVal(mass)
        ws.var('mtop_m%s'%iCat).setConstant(True)

    # The combined dataset
    getattr(ws,'import')( ROOT.RooDataHist("combcorrect","combcorrect",
                            ROOT.RooArgList(mbl),
                            ROOT.RooFit.Index( ws.cat('sig_mass_cats') ),
                            ROOT.RooFit.Import("m1665", correctH['1665'] ),
                            ROOT.RooFit.Import("m1695", correctH['1695'] ),
                            ROOT.RooFit.Import("m1725", correctH['1725'] ),
                            ROOT.RooFit.Import("m1735", correctH['1735'] ),
                            ROOT.RooFit.Import("m1755", correctH['1755'] ),
                            ROOT.RooFit.Import("m1785", correctH['1785'] ) ) )

    # Now fit...
    fitresult = ws.pdf('sigmodel_sim').fitTo(ws.data('combcorrect'),
                                             ROOT.RooFit.Save(True))

    # cov = fitresult.covarianceMatrix()
    # cor = fitresult.correlationMatrix()

    #
    # parameterization for wrong combinations
    #
    ws.factory("SUM::sig_wrong(sig_wrong_frac[0.9,0,1.0]*"
                   "BifurGauss::sig_wrong_agauss(mbl,"
                      "sig_wrong_agauss_mean[70,0,100],"
                      "sig_wrong_agauss_sigmaL[20,0,50],"
                      "sig_wrong_agauss_sigmaR[70,20,100]),"
                   "RooGamma::sig_wrong_ngauss(mbl,"
                      "sig_wrong_ngauss_gamma[3.2,2.5,4.0],"
                      "sig_wrong_ngauss_beta[14,10,20],"
                      "sig_wrong_ngauss_mu[8,0,15]))")
    # raw_input()
    ws.pdf('sig_wrong').fitTo(ws.data('wrong'), ROOT.RooFit.Save(True))

    # These are the current values
    ws.saveSnapshot("model_params", ws.allVars(), True)

    # Save workspace to file and return the name
    wsFile = os.path.join(outdir, 'mSVL_Workspace_%s.root'%selection)
    ws.writeToFile(wsFile)
    print 80*'-'
    print 'Workspace has been created and stored @ %s'%wsFile
    print 80*'-'

    return ws


def showWorkspace(ws,selection,outdir,outformats=['pdf']):
"""
    And show
"""
    os.system('mkdir -p %s' % outdir)
    ROOT.gROOT.SetBatch(1)

    c = ROOT.TCanvas('c1','c1',1200,900)

    leftMargin = 0.15*(1./3.)
    deltaX = (1.-leftMargin)/3.
    xini,xfin = 0,deltaX+leftMargin
    bottomMargin = 0.05
    deltaY = (1.-bottomMargin)/2.
    yini,yfin = 0,deltaY+bottomMargin

    iCatCtr=0
    # for mass in MASSES:
    #     iCat = str(mass).replace('.','')
    for iCat in ["m1735","m1755","m1785","m1665","m1695","m1725"]:
        mass = float(iCat[1:-1]+".5")
        c.cd()
        p1 = ROOT.TPad('p2%d'%iCatCtr,'p2',xini,yini,xfin,yfin-0.15)
        p1.Draw()
        p1.cd()
        p1.SetRightMargin(0.005)
        p1.SetLeftMargin(0.008)
        p1.SetTopMargin(0.008)
        p1.SetBottomMargin(0.005)
        if iCatCtr==0 or iCatCtr==3: p1.SetLeftMargin(0.15)
        if iCatCtr<3: p1.SetBottomMargin(0.2)
        p1.SetGridx(True)

        frame = ws.var('mbl').frame()
        redData = ws.data('combcorrect').reduce(
                    ROOT.RooFit.Cut("sig_mass_cats==sig_mass_cats::%s"%iCat))
        redData.plotOn(frame)
        ws.cat('sig_mass_cats').setLabel(iCat)
        ws.cat('sig_mass_cats')
        ws.pdf('sigmodel_sim').plotOn(frame,
                                      ROOT.RooFit.Slice(
                                           ws.cat('sig_mass_cats'),iCat),
                                      ROOT.RooFit.ProjWData(redData),
                                      ROOT.RooFit.Components('sig_ngauss*'),
                                      ROOT.RooFit.LineColor(920),
                                      ROOT.RooFit.LineWidth(1))

        ws.pdf('sigmodel_sim').plotOn(frame,
                                      ROOT.RooFit.Slice(
                                           ws.cat('sig_mass_cats'),iCat),
                                      ROOT.RooFit.ProjWData(redData))


        frame.Draw()
        frame.GetYaxis().SetTitle("Entries")
        frame.GetYaxis().SetTitleSize(0)
        frame.GetYaxis().SetLabelSize(0)
        if iCatCtr==0 or iCatCtr==3:
            frame.GetYaxis().SetTitleSize(0.07)
            frame.GetYaxis().SetLabelSize(0.07)
        if iCatCtr<3:
            frame.GetXaxis().SetTitle("m(SV,lepton) [GeV]")
            frame.GetXaxis().SetTitleSize(0.06)
            frame.GetXaxis().SetLabelSize(0.06)
        else:
            frame.GetXaxis().SetTitleSize(0)
            frame.GetXaxis().SetLabelSize(0)
        label = ROOT.TLatex()
        label.SetNDC()
        label.SetTextFont(42)
        label.SetTextSize(0.06)
        label.DrawLatex(0.72,0.9,'[%3.1f GeV]'%mass)
        label.DrawLatex(0.72,0.8,'#chi^{2}=%3.2f'%frame.chiSquare())

        c.cd()
        p2=ROOT.TPad('p2%d'%iCatCtr,'p2',xini,yfin-0.15,xfin,yfin)
        p2.Draw()
        p2.cd()
        p2.SetBottomMargin(0.005)
        p2.SetRightMargin(0.005)
        p2.SetLeftMargin(0.008)
        p2.SetTopMargin(0.4)
        if iCatCtr==0 or iCatCtr==3: p2.SetLeftMargin(0.15)
        p2.SetGridx(True)
        p2.SetGridy(True)

        hpull = frame.pullHist()
        pullFrame = ws.var('mbl').frame()
        pullFrame.addPlotable(hpull,"P") ;
        pullFrame.Draw()
        pullFrame.GetYaxis().SetTitle("#frac{Data-Fit}{#sigma}")
        pullFrame.GetYaxis().SetTitleSize(0)
        pullFrame.GetYaxis().SetLabelSize(0)
        if iCatCtr==0 or iCatCtr==3:
            pullFrame.GetYaxis().SetTitleSize(0.15)
            pullFrame.GetYaxis().SetLabelSize(0.15)
        pullFrame.GetXaxis().SetTitleSize(0)
        pullFrame.GetXaxis().SetLabelSize(0)
        pullFrame.GetYaxis().SetTitleOffset(0.4)
        pullFrame.GetYaxis().SetNdivisions(4)
        pullFrame.GetYaxis().SetRangeUser(-3.1,3.1)
        pullFrame.GetXaxis().SetTitleOffset(0.8)

        if iCatCtr==4:
            label=ROOT.TLatex()
            label.SetNDC()
            label.SetTextFont(42)
            label.SetTextSize(0.1)
            label.DrawLatex(0.1,0.8,'CMS simulation, signal model'
                                    '(correct permutations)')

        iCatCtr = iCatCtr+1
        xini = xfin
        xfin += deltaX
        if xfin>1 : xini,xfin=0,deltaX+leftMargin
        if iCatCtr == 3:
            yini = yfin
            yfin += deltaY

    c.Modified()
    c.Update()

    outname = os.path.join(outdir,'SignalModel_%s_CorrectPermutations'%
                                                             (selection))
    for ext in outformats : c.SaveAs("%s.%s" % (outname,ext))

    c.Clear()
    c.SetWindowSize(500,500)
    p1 = ROOT.TPad('p1','p1',0,0,1.0,0.8)
    p1.Draw()
    p1.cd()
    p1.SetTopMargin(0.005)
    p1.SetGridx(True)
    frame=ws.var('mbl').frame()
    ws.data('wrong').plotOn(frame)
    ws.pdf('sig_wrong').plotOn(frame,
                               ROOT.RooFit.Components('sig_wrong_ngauss*'),
                               ROOT.RooFit.LineColor(920),
                               ROOT.RooFit.LineWidth(1) )
    ws.pdf('sig_wrong').plotOn(frame)
    frame.Draw()
    frame.GetXaxis().SetTitle("m(SV,lepton) [GeV]")
    frame.GetYaxis().SetTitle('Entries')
    frame.GetYaxis().SetTitleSize(0.04)
    frame.GetXaxis().SetTitleSize(0.04)
    frame.GetYaxis().SetLabelSize(0.04)
    frame.GetYaxis().SetTitleOffset(1.2)
    frame.GetXaxis().SetLabelSize(0.04)

    label=ROOT.TLatex()
    label.SetNDC()
    label.SetTextFont(42)
    label.SetTextSize(0.06)
    label.DrawLatex(0.72,0.9,'#chi^{2}=%3.2f'%frame.chiSquare())

    c.cd()
    p2 = ROOT.TPad('p2','p2',0,0.8,1,1)
    p2.Draw()
    p2.cd()
    p2.SetTopMargin(0.4)
    p2.SetBottomMargin(0.005)
    p2.SetGridx(True)
    p2.SetGridy(True)
    hpull = frame.pullHist()
    pullFrame = ws.var('mbl').frame()
    pullFrame.addPlotable(hpull,"P") ;
    pullFrame.Draw()
    pullFrame.GetYaxis().SetTitle("#frac{Data-Fit}{#sigma}")
    pullFrame.GetYaxis().SetTitleSize(0.15)
    pullFrame.GetYaxis().SetLabelSize(0.15)
    pullFrame.GetXaxis().SetTitleSize(0)
    pullFrame.GetXaxis().SetLabelSize(0)
    pullFrame.GetYaxis().SetTitleOffset(0.4)
    pullFrame.GetYaxis().SetNdivisions(4)
    pullFrame.GetYaxis().SetRangeUser(-3.1,3.1)
    pullFrame.GetYaxis().SetTitleOffset(0.25)

    label=ROOT.TLatex()
    label.SetNDC()
    label.SetTextFont(42)
    label.SetTextSize(0.15)
    label.DrawLatex(0.1,0.8,'CMS simulation, signal model (wrong permutations)')

    c.Modified()
    c.Update()
    outname = os.path.join(outdir,'SignalModel_%s_WrongPermutations'%
                                                             (selection))
    for ext in outformats : c.SaveAs("%s.%s" % (outname,ext))

def plotParameters(ws, outdir):
"""
    Plot the fit parameters as a function of mt
"""
    os.system('mkdir -p %s'%outdir)

    ROOT.gROOT.SetBatch(1)
    pars_to_plot = ["sig_agauss_mean", "sig_agauss_sigmaL",
                    "sig_agauss_sigmaR","sig_ngauss_beta",
                    "sig_ngauss_gamma", "sig_ngauss_mu"]

    colors = [51, 62, 83, 93, 100, 68]

    for np,param in enumerate(pars_to_plot):
        par1 = ws.var("b_%s"% param).getVal()
        par2 = ws.var("a_%s"% param).getVal()
        par1E = ws.var("b_%s"% param).getError()
        par2E = ws.var("a_%s"% param).getError()

        canv = ROOT.TCanvas('C_%s'%param,'c',800,800)
        canv.cd()
        axes = ROOT.TH2D("axes_%s"%param, "axes",
                          1, -15., 15,
                          1, (1-0.23)*par1, (1+0.23)*par1)
        axes.GetXaxis().SetTitle("#Delta m_{top} [GeV]")
        axes.Draw("axis")

        nom = ROOT.TF1("nom_%s"%param, "pol1", -20., 20.)
        nom.SetParameters(par1, par2)

        upup = ROOT.TF1("upup_%s"%param, "pol1", -20., 20.)
        upup.SetParameters(par1+par1E, par2+par2E)
        dndn = ROOT.TF1("dndn_%s"%param, "pol1", -20., 20.)
        dndn.SetParameters(par1-par1E, par2-par2E)
        updn = ROOT.TF1("updn_%s"%param, "pol1", -20., 20.)
        updn.SetParameters(par1+par1E, par2-par2E)
        dnup = ROOT.TF1("dnup_%s"%param, "pol1", -20., 20.)
        dnup.SetParameters(par1-par1E, par2+par2E)

        nom.SetLineWidth(3)
        for x in [nom, upup, updn, dndn, dnup]:
            x.SetLineColor(colors[np])
        for x in [upup,dnup,updn,dndn]:
            x.SetLineWidth(1)
            x.SetLineStyle(2)
        upup.DrawCopy("same")
        dndn.DrawCopy("same")
        updn.DrawCopy("same")
        dnup.DrawCopy("same")
        nom.DrawCopy("same")

        label=ROOT.TLatex()
        label.SetNDC()
        label.SetTextFont(42)
        label.SetTextSize(0.03)
        label.DrawLatex(0.15,0.83, param)

        outname = os.path.join(outdir, "calib_%s.pdf"%param)
        canv.SaveAs(outname)


def runPseudoExperiments(ws,peFileName,nTotal,fCorrect,nPexp):
"""
    run pseudo-experiments
"""

    #load the model parameters and set all to constant
    ws.loadSnapshot("model_params")
    allVars=ws.allVars()
    varIter = allVars.createIterator()
    var = varIter.Next()
    print 'Setting to constant:',
    while var :
        varName=var.GetName()
        if not varName in ['mtop', 'mbl']:
            ws.var(varName).setConstant(True)
            print varName,
        var = varIter.Next()

    #create the fit model
    ws.factory('nCorrect[%f,%f,%f]'%(nTotal*fCorrect,0,2*nTotal))
    ws.factory('nWrong[%f,%f,%f]'%(nTotal*(1-fCorrect),0,2*nTotal))
    ws.factory("SUM::mtopfit( nCorrect*sigmodel, nWrong*sig_wrong )")

    #pseudo-experiments
    wrongH=ws.data('wrong').createHistogram('mbl')
    wrongH.SetName('wrongH')
    fitBiasesH={}
    fitStatUncH={}
    fitPullH={}
    for mass in MASSES:
        iCat = str(mass).replace('.','')

        trueMtop=float(iCat.replace('m','').replace('v','.'))
        fitBiasesH[trueMtop]=ROOT.TH1F(iCat+'_biasH',';m_{t}-m_{t}^{true} [GeV];Pseudo-experiments',100,-2.02,1.98)
        fitBiasesH[trueMtop].SetDirectory(0)
        fitStatUncH[trueMtop]=ROOT.TH1F(iCat+'_statuncH',';#sigma(m_{t}) [GeV];Pseudo-experiments',200,0,2.0)
        fitStatUncH[trueMtop].SetDirectory(0)
        fitPullH[trueMtop]=ROOT.TH1F(iCat+'_pullH',';(m_{t}-m_{t}^{true})/#sigma(m_{t});Pseudo-experiments',100,-2.02,1.98)
        fitPullH[trueMtop].SetDirectory(0)

        #correct assignments for new top mass
        redData=ws.data('combcorrect').reduce( ROOT.RooFit.Cut("sig_mass_cats==sig_mass_cats::%s"%iCat) )
        correctH=redData.createHistogram('mbl')
        correctH.SetName(iCat+'correctH')

        pseudoDataH=correctH.Clone(iCat+'pseudoDataH')
        for i in xrange(0,nPexp):

            #generate new pseudo-data
            pseudoDataH.Reset('ICE')
            for nev in xrange(0,ROOT.gRandom.Poisson(nTotal*fCorrect))     : pseudoDataH.Fill(correctH.GetRandom())
            for nev in xrange(0,ROOT.gRandom.Poisson(nTotal*(1-fCorrect))) : pseudoDataH.Fill(wrongH.GetRandom())
            pseudoData=ROOT.RooDataHist('pseudoData','pseudoData',ROOT.RooArgList(ws.var('mbl')),pseudoDataH)

            ws.pdf('mtopfit').fitTo(pseudoData,ROOT.RooFit.Extended())
            mtopFit=ws.var('mtop')

            #create the likelihood
            #nll = ws.pdf('mtopfit').createNLL(pseudoData,ROOT.RooFit.Extended())
            #ROOT.RooMinuit(nll).migrad() ;

            #profile mtop
            #pll = nll.createProfile(ROOT.RooArgSet(ws.var('mtop')))
            #ROOT.RooMinuit(pll).migrad()
            #mtopFit=pll.bestFitObs().find('mtop')

            fitBiasesH[trueMtop].Fill(mtopFit.getVal()-trueMtop)
            fitStatUncH[trueMtop].Fill(mtopFit.getError())
            fitPullH[trueMtop].Fill((mtopFit.getVal()-trueMtop)/mtopFit.getError())

    #save results to a file
    peFile=ROOT.TFile(peFileName,'RECREATE')
    for cat in fitBiasesH:
        fitBiasesH[cat].Fit('gaus','LMQ+')
        fitBiasesH[cat].SetDirectory(peFile)
        fitBiasesH[cat].Write()
        fitStatUncH[cat].SetDirectory(peFile)
        fitStatUncH[cat].Write()
        fitPullH[cat].Fit('gaus','LMQ+')
        fitPullH[cat].SetDirectory(peFile)
        fitPullH[cat].Write()
    peFile.Close()


"""
steer
"""
def main():
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-s', '--selection', dest='selection',
                       default='drrank',
                       help=('Selection type. [mrank, drrank, mrankinc, '
                             ' drrankinc, mrank12, drrank12]'))
    parser.add_option('-i', '--input', dest='input',
                       default='histos.root',
                       help='input file with histograms.')
    parser.add_option('-w', '--ws', dest='wsFile', default=None,
                       help='ROOT file with previous workspace.')
    parser.add_option('-n', '--nPexp', dest='nPexp', default=250, type=int,
                       help='Total # pseudo-experiments.')
    parser.add_option('-t', '--nTotal', dest='nTotal', default=66290,
                       type=float, help='Total # events.')
    parser.add_option('-f', '--fCorrect', dest='fCorrect', default=0.75,
                       type=float, help='Fraction of correct assignments.')
    parser.add_option('-o', '--outDir', dest='outDir', default='svlfits',
                       help='Output directory [default: %default]')

    (opt, args) = parser.parse_args()

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)

    # Check if one needs to create a new workspace or run pseudo-experiments
    if opt.wsFile is None :
        print 80*'-'
        print 'Creating a new workspace file for selection=%s' %opt.selection
        sigFile = opt.input
        ws = createWorkspace(sigFile=sigFile,
                             selection=opt.selection,
                             outdir=opt.outDir)

    else:
        inF = ROOT.TFile.Open(opt.wsFile)
        ws = inF.Get('w')
        inF.Close()

    # Make the plots
    showWorkspace(ws=ws, selection=opt.selection, outdir=opt.outDir)
    plotParameters(ws=ws, outdir=opt.outDir)

    doPEs = True
    if doPEs:
        print 80*'-'
        print ('Running pseudo-experiments for workspace retrieved from %s'
                 % opt.wsFile)
        runPseudoExperiments(ws=ws,
                             peFileName=opt.wsFile.replace('.root','_pe.root'),
                             nTotal=opt.nTotal,
                             fCorrect=opt.fCorrect,
                             nPexp=opt.nPexp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
