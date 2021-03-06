#!/usr/bin/env python
import ROOT
import os,sys
import os.path as osp
import optparse
import pickle
import numpy

from UserCode.TopMassSecVtx.PlotUtils import printProgress, bcolors
from makeSVLMassHistos import NTRKBINS

"""
Wrapper to contain the histograms with the results of the pseudo-experiments
"""
class PseudoExperimentResults:

    def __init__(self,genMtop,outFileUrl,
                 dmrange=(-5.0,5.0),
                 statuncrange=(0,1.5),
                 pullrange=(-3.03,2.97),
                 murange=(0.85,1.15)):
        self.genMtop=genMtop
        self.outFileUrl=outFileUrl
        self.histos={}
        self.trees={}

        self.dmrange      = dmrange
        self.statuncrange = statuncrange
        self.pullrange    = pullrange
        self.murange      = murange

        self.genmtop = numpy.zeros(1, dtype=float)
        self.genmtop[0] = self.genMtop
        self.mtopfit = numpy.zeros(1, dtype=float)
        self.statunc = numpy.zeros(1, dtype=float)
        self.pull    = numpy.zeros(1, dtype=float)
        self.mu      = numpy.zeros(1, dtype=float)

    def addFitResult(self,key,ws):

        #init histogram if needed
        if not (key in self.histos):
            self.initHistos(key)

        #fill the histograms
        if ws.var('mtop').getError()>0:
            mtopfit = ws.var('mtop').getVal()
            bias = mtopfit-self.genMtop
            error = ws.var('mtop').getError()
            self.mtopfit[0] = mtopfit
            self.statunc[0] = error
            self.pull   [0] = bias/error
            self.mu     [0] = ws.var('mu').getVal()

            self.histos[key]['mtopfit']        .Fill(bias)
            self.histos[key]['mtopfit_statunc'].Fill(error)
            self.histos[key]['mtopfit_pull']   .Fill(bias/error)
            self.histos[key]['muvsmtop']       .Fill(bias, ws.var('mu').getVal())
            self.trees[key].Fill()

    def initHistos(self,key):
        self.histos[key]={}
        pfix=key
        # pfix=''
        # for tk in key: pfix += str(tk)+'_'
        # pfix=pfix[:-1]
        self.histos[key]['mtopfit']         = ROOT.TH1F('mtopfit_%s'%pfix,
                                                        ';#Deltam_{t} [GeV];Pseudo-experiments',
                                                        200,self.dmrange[0],self.dmrange[1])
        self.histos[key]['mtopfit_statunc'] = ROOT.TH1F('mtopfit_statunc_%s'%pfix,
                                                        ';#sigma_{stat}(m_{t}) [GeV];Pseudo-experiments',
                                                        200,self.statuncrange[0],self.statuncrange[1])
        self.histos[key]['mtopfit_pull']    = ROOT.TH1F('mtopfit_pull_%s'%pfix,
                                                        ';Pull=(m_{t}-m_{t}^{true})/#sigma_{stat}(m_{t});Pseudo-experiments',
                                                        100,self.pullrange[0],self.pullrange[1])
        self.histos[key]['muvsmtop']        = ROOT.TH2F('muvsmtop_%s'%pfix,
                                                        ';#Delta m_{t} [GeV];#mu=#sigma/#sigma_{th}(172.5 GeV);Pseudo-experiments',
                                                        100,self.dmrange[0],self.dmrange[1],
                                                        100,self.murange[0],self.murange[1])
        for var in self.histos[key]:
            self.histos[key][var].SetDirectory(0)
            self.histos[key][var].Sumw2()

        self.trees[key] = ROOT.TTree('peinfo_%s'%pfix,'SVL Pseudoexperiment info')
        self.trees[key].Branch('genmtop', self.genmtop, 'genmtop/D')
        self.trees[key].Branch('mtopfit', self.mtopfit, 'mtopfit/D')
        self.trees[key].Branch('statunc', self.statunc, 'statunc/D')
        self.trees[key].Branch('pull',    self.pull,    'pull/D')
        self.trees[key].Branch('mu',      self.mu,      'mu/D')



    def saveResults(self):
        peFile=ROOT.TFile(self.outFileUrl,'RECREATE')
        for key in self.histos:
            dirName=key
            # dirName=''
            # for tk in key: dirName+=str(tk)+'_'
            # dirName=dirName[:-1]
            peFile.cd()
            outDir=peFile.mkdir(dirName)
            outDir.cd()
            for var in self.histos[key]:
                self.histos[key][var].Write()
            self.trees[key].Write()

            mtopRes=ROOT.TVectorD(6)
            mtopRes[0]=self.histos[key]['mtopfit'].GetMean()
            mtopRes[1]=self.histos[key]['mtopfit'].GetMeanError()
            mtopRes[2]=self.histos[key]['mtopfit_statunc'].GetMean()
            mtopRes[3]=self.histos[key]['mtopfit_statunc'].GetMeanError()
            mtopRes[4]=self.histos[key]['mtopfit_pull'].GetMean()
            mtopRes[5]=self.histos[key]['mtopfit_pull'].GetRMS()
            mtopRes.Write('mtop')

            peFile.cd()

        #all done here
        peFile.cd()
        peFile.Close()


"""
Show PE fit result
"""
def showFinalFitResult(data,pdf,nll,SVLMass,mtop,outDir,tag=None):
    #init canvas
    canvas=ROOT.TCanvas('c','c',500,500)

    p1 = ROOT.TPad('p1','p1',0.0,0.85,1.0,0.0)
    p1.SetRightMargin(0.05)
    p1.SetLeftMargin(0.12)
    p1.SetTopMargin(0.01)
    p1.SetBottomMargin(0.1)
    p1.Draw()
    
    #fit results
    p1.cd()
    frame=SVLMass.frame()
    data.plotOn(frame,ROOT.RooFit.Name('data'))
    pdf.plotOn(frame,
               ROOT.RooFit.Name('totalexp'),
               ROOT.RooFit.ProjWData(data),
               ROOT.RooFit.LineColor(ROOT.kBlue),
               ROOT.RooFit.LineWidth(2),
               ROOT.RooFit.MoveToBack())
    pdf.plotOn(frame,
               ROOT.RooFit.Name('singlet'),
               ROOT.RooFit.ProjWData(data),
               #ROOT.RooFit.Components('tshape_*'),
               ROOT.RooFit.Components('simplemodel_*_t'),
               ROOT.RooFit.FillColor(ROOT.kOrange+2),
               ROOT.RooFit.LineColor(ROOT.kOrange+2),
               ROOT.RooFit.FillStyle(1001),
               ROOT.RooFit.DrawOption('f'),
               ROOT.RooFit.MoveToBack())
    pdf.plotOn(frame,
               ROOT.RooFit.Name('tt'),
               ROOT.RooFit.ProjWData(data),
               ROOT.RooFit.Components('simplemodel_*_tt'),
               #ROOT.RooFit.Components('ttshape_*,tshape_*'),
               #ROOT.RooFit.Components('*_ttcor_*'),
               ROOT.RooFit.FillColor(ROOT.kOrange),
               ROOT.RooFit.LineColor(ROOT.kOrange),
               ROOT.RooFit.DrawOption('f'),
               ROOT.RooFit.FillStyle(1001),
               ROOT.RooFit.MoveToBack())
    frame.Draw()
    frame.GetYaxis().SetTitleOffset(1.5)
    frame.GetXaxis().SetTitle("m(SV,lepton) [GeV]")
    label=ROOT.TLatex()
    label.SetNDC()
    label.SetTextFont(42)
    label.SetTextSize(0.04)
    label.DrawLatex(0.18,0.94,'#bf{CMS} #it{simulation}')
    leg=ROOT.TLegend(0.65,0.35,0.95,0.52)
    leg.AddEntry('data',       'Pseudo data',      'p')
    leg.AddEntry('totalexp',   'Total',     'l')
    leg.AddEntry('tt',         't#bar{t}',  'f')
    leg.AddEntry('singlet',    'Single top','f')
    leg.SetFillStyle(0)
    leg.SetTextFont(43)
    leg.SetTextSize(14)
    leg.SetBorderSize(0)
    leg.Draw()
    ROOT.SetOwnership(leg,0)

    if tag:
        tlat = ROOT.TLatex()
        tlat.SetTextFont(43)
        tlat.SetNDC(1)
        tlat.SetTextAlign(13)
        tlat.SetTextSize(14)
        if type(tag) == str:
            tlat.DrawLatex(0.65, 0.32, tag)
        else:
            ystart = 0.32
            yinc = 0.05
            for n,text in enumerate(tag):
                tlat.DrawLatex(0.65, ystart-n*yinc, text)


    canvas.cd()
    p2 = ROOT.TPad('p2','p2',0.0,0.86,1.0,1.0)
    p2.SetBottomMargin(0.05)
    p2.SetRightMargin(0.05)
    p2.SetLeftMargin(0.12)
    p2.SetTopMargin(0.05)
    p2.Draw()
    p2.cd()
    hpull = frame.pullHist()
    pullFrame = SVLMass.frame()
    pullFrame.addPlotable(hpull,"P") ;
    pullFrame.Draw()
    pullFrame.GetYaxis().SetTitle("Pull")
    pullFrame.GetYaxis().SetTitleSize(0.2)
    pullFrame.GetYaxis().SetLabelSize(0.2)
    pullFrame.GetXaxis().SetTitleSize(0)
    pullFrame.GetXaxis().SetLabelSize(0)
    pullFrame.GetYaxis().SetTitleOffset(0.15)
    pullFrame.GetYaxis().SetNdivisions(4)
    pullFrame.GetYaxis().SetRangeUser(-3.1,3.1)
    pullFrame.GetXaxis().SetTitleOffset(0.8)

    canvas.cd()
    p3 = ROOT.TPad('p3','p3',0.6,0.47,0.95,0.82)
    p3.SetRightMargin(0.05)
    p3.SetLeftMargin(0.12)
    p3.SetTopMargin(0.008)
    p3.SetBottomMargin(0.2)
    p3.Draw()
    p3.cd()
    frame2=mtop.frame()
    for ill in xrange(0,len(nll)): nll[ill].plotOn(frame2,ROOT.RooFit.ShiftToZero(),ROOT.RooFit.LineStyle(ill+1))
    frame2.Draw()
    frame2.GetYaxis().SetRangeUser(0,12)
    frame2.GetXaxis().SetRangeUser(165,180)
    frame2.GetYaxis().SetNdivisions(3)
    frame2.GetXaxis().SetNdivisions(3)
    frame2.GetXaxis().SetTitle('Top mass [GeV]')
    frame2.GetYaxis().SetTitle('pLL and LL')
    frame2.GetYaxis().SetTitleOffset(1.5)
    frame2.GetXaxis().SetTitleSize(0.08)
    frame2.GetXaxis().SetLabelSize(0.08)
    frame2.GetYaxis().SetTitleSize(0.08)
    frame2.GetYaxis().SetLabelSize(0.08)

    canvas.Modified()
    canvas.Update()
    canvas.SaveAs('%s/plots/%s_fit.png'%(outDir,data.GetName()))
    canvas.SaveAs('%s/plots/%s_fit.pdf'%(outDir,data.GetName()))
    canvas.Delete()

"""
run pseudo-experiments
"""
def runPseudoExperiments(wsfile,pefile,experimentTag,options):

    #read the file with input distributions
    inputDistsF = ROOT.TFile.Open(pefile, 'READ')
    prepend = '[runPseudoExperiments %s] '%experimentTag
    print prepend+'Reading PE input from %s' % pefile
    print prepend+'with %s' % experimentTag

    wsInputFile = ROOT.TFile.Open(wsfile, 'READ')
    ws = wsInputFile.Get('w')
    wsInputFile.Close()
    print prepend+'Read workspace from %s' % wsfile

    #readout calibration from a file
    calibMap=None
    if options.calib:
         cachefile = open(options.calib,'r')
         calibMap  = pickle.load(cachefile)
         cachefile.close()
         print prepend+'Read calibration from %s'%options.calib

    genMtop=172.5
    try:
        genMtop=float(experimentTag.rsplit('_', 1)[1].replace('v','.'))
    except Exception, e:
        raise e
    print prepend+'Generated top mass is %5.1f GeV'%genMtop

    #prepare results summary
    selTag=''
    if len(options.selection)>0 : selTag='_%s'%options.selection
    summary=PseudoExperimentResults(genMtop=genMtop,
                                    outFileUrl=osp.join(options.outDir,'%s%s_results.root'%(experimentTag,selTag)))

    #load the model parameters and set all to constant
    ws.loadSnapshot("model_params")
    allVars = ws.allVars()
    varIter = allVars.createIterator()
    var = varIter.Next()
    varCtr=0
    while var :
        varName=var.GetName()
        if not varName in ['mtop', 'SVLMass', 'mu']:
        #if not varName in ['mtop', 'SVLMass']:
            ws.var(varName).setConstant(True)
            varCtr+=1
        var = varIter.Next()
    print prepend+'setting to constant %d numbers in the model'%varCtr

    #build the relevant PDFs
    allPdfs = {}
    finalStates=['em','mm','ee','m','e']
    for ch in finalStates:
        chsel=ch
        if len(options.selection)>0 : chsel += '_' + options.selection
        for ntrk in [tklow for tklow,_ in NTRKBINS]: # [2,3,4]
            ttexp      = '%s_ttexp_%d'              %(chsel,ntrk)
            ttcor      = '%s_ttcor_%d'              %(chsel,ntrk)
            ttcorPDF   = 'simplemodel_%s_%d_cor_tt' %(chsel,ntrk)
            ttwro      = '%s_ttwro_%d'              %(chsel,ntrk)
            ttwroPDF   = 'simplemodel_%s_%d_wro_tt' %(chsel,ntrk)
            ttunmPDF   = 'model_%s_%d_unm_tt'       %(chsel,ntrk)
            tfrac      = '%s_tfrac_%d'              %(chsel,ntrk)
            tcor       = '%s_tcor_%d'               %(chsel,ntrk)
            tcorPDF    = 'simplemodel_%s_%d_cor_t'  %(chsel,ntrk)
            twrounmPDF = 'model_%s_%d_wrounm_t'     %(chsel,ntrk)
            bkgExp     = '%s_bgexp_%d'              %(chsel,ntrk)
            bkgPDF     = 'model_%s_%d_unm_bg'       %(chsel,ntrk)

            ttShapePDF = ws.factory("SUM::ttshape_%s_%d(%s*%s,%s*%s,%s)"%(chsel,ntrk,ttcor,ttcorPDF,ttwro,ttwroPDF,ttunmPDF))
            Ntt        = ws.factory("RooFormulaVar::Ntt_%s_%d('@0*@1',{mu,%s})"%(chsel,ntrk,ttexp))

            tShapePDF  = ws.factory("SUM::tshape_%s_%d(%s*%s,%s)"%(chsel,ntrk,tcor,tcorPDF,twrounmPDF))
            Nt         = ws.factory("RooFormulaVar::Nt_%s_%d('@0*@1*@2',{mu,%s,%s})"%(chsel,ntrk,ttexp,tfrac))

            bkgConstPDF = ws.factory('Gaussian::bgprior_%s_%d(bg0_%s_%d[0,-10,10],bg_nuis_%s_%d[0,-10,10],1.0)'%(chsel,ntrk,chsel,ntrk,chsel,ntrk))
            ws.var('bg0_%s_%d'%(chsel,ntrk)).setVal(0.0)
            ws.var('bg0_%s_%d'%(chsel,ntrk)).setConstant(True)
            #ws.var('bg_nuis_%s_%d'%(chsel,ntrk)).setVal(0.0)
            #ws.var('bg_nuis_%s_%d'%(chsel,ntrk)).setConstant(True)

            #30% unc on background
            Nbkg        =  ws.factory("RooFormulaVar::Nbkg_%s_%d('@0*max(1+0.30*@1,0.)',{%s,bg_nuis_%s_%d})"%(chsel,ntrk,bkgExp,chsel,ntrk))
            # print '[Expectation] %2s, %d: %8.2f' % (chsel, ntrk, Ntt.getVal()+Nt.getVal()+Nbkg.getVal())

            #see syntax here https://root.cern.ch/root/html/RooFactoryWSTool.html#RooFactoryWSTool:process
            sumPDF = ws.factory("SUM::uncalibexpmodel_%s_%d( %s*%s, %s*%s, %s*%s )"%(chsel,ntrk,
                                                                              Ntt.GetName(), ttShapePDF.GetName(),
                                                                              Nt.GetName(), tShapePDF.GetName(),
                                                                              Nbkg.GetName(), bkgPDF
                                                                              ))
            ws.factory('PROD::uncalibmodel_%s_%d(%s,%s)'%(chsel,ntrk,
                                                          sumPDF.GetName(),
                                                          bkgConstPDF.GetName()))

            #add calibration for this category if available (read from a pickle file)
            offset, slope = 0.0, 1.0
            if calibMap:
                try:
                    offset, slope = calibMap[options.selection][ '%s_%d'%(ch,ntrk) ]
                except KeyError, e:
                    print 'Failed to retrieve calibration with',e
            ws.factory("RooFormulaVar::calibmtop_%s_%d('(@0-%f)/%f',{mtop})"%(chsel,ntrk,offset,slope))
            allPdfs[(chsel,ntrk)] = ws.factory("EDIT::model_%s_%d(uncalibmodel_%s_%d,mtop=calibmtop_%s_%d)"%
                                               (chsel,ntrk,chsel,ntrk,chsel,ntrk))

    #throw pseudo-experiments
    poi = ROOT.RooArgSet( ws.var('mtop') )
    if options.verbose>1:
        print prepend+'Running %d experiments' % options.nPexp
        print 80*'-'

    if not 'nominal' in experimentTag:
        cfilepath = osp.abspath(osp.join(osp.dirname(wsfile),'../../'))
        cfilepath = osp.join(cfilepath, ".svlsysthistos.pck")
        cachefile = open(cfilepath, 'r')
        systhistos = pickle.load(cachefile)
        print prepend+'>>> Read systematics histograms from cache (.svlsysthistos.pck)'
        cachefile.close()

    for i in xrange(0,options.nPexp):

        #iterate over available categories to build the set of likelihoods to combine
        nllMap={}
        allPseudoDataH=[]
        allPseudoData=[]
        if options.verbose>1 and options.verbose<=3:
            printProgress(i, options.nPexp, prepend+' ')

        for key in sorted(allPdfs):
            chsel, trk = key
            mukey=(chsel+'_mu',trk)
            if options.verbose>3:
                sys.stdout.write(prepend+'Exp %-3d (%-2s, %d):' % (i+1, chsel, trk))
                sys.stdout.flush()

            ws.var('mtop').setVal(172.5)
            ws.var('mu').setVal(1.0)

            #read histogram and generate random data
            ihist = inputDistsF.Get('%s/SVLMass_%s_%s_%d'%(experimentTag,chsel,experimentTag,trk))

            # Get number of events to be generated either:
            # - From properly scaled input files for nominal mass variations
            #   to estimate the actual statistical error
            # - From the number of generated MC events, to estimate statistical
            #   uncertainty of variation
            nevtsSeed = ihist.Integral()
            if not 'nominal' in experimentTag:
                try:
                    nevtsSeed = systhistos[(chsel, experimentTag.replace('_172v5',''),
                                            'tot' ,trk)].GetEntries() ## FIXME: GetEntries or Integral?
                except KeyError:
                    print prepend+"  >>> COULD NOT FIND SYSTHISTO FOR",chsel, experimentTag, trk

            nevtsToGen = ROOT.gRandom.Poisson(nevtsSeed)


            pseudoDataH,pseudoData=None,None
            if options.genFromPDF:
                obs = ROOT.RooArgSet(ws.var('SVLMass'))
                pseudoData = allPdfs[key].generateBinned(obs, nevtsToGen)
            else:
                pseudoDataH = ihist.Clone('peh')
                if options.nPexp>1:
                    pseudoDataH.Reset('ICE')
                    pseudoDataH.FillRandom(ihist, nevtsToGen)
                else:
                    print 'Single pseudo-experiment won\'t be randomized'
                pseudoData  = ROOT.RooDataHist('PseudoData_%s_%s_%d'%(experimentTag,chsel,trk),
                                               'PseudoData_%s_%s_%d'%(experimentTag,chsel,trk),
                                               ROOT.RooArgList(ws.var('SVLMass')), pseudoDataH)

            if options.verbose>3:
                sys.stdout.write(' [generated pseudodata]')
                sys.stdout.flush()

            #create likelihood
            #store it in the appropriate categories for posterior combination
            for nllMapKey in [('comb',0),('comb',trk),('comb%s'%chsel,0)]:
                if not (nllMapKey in nllMap):
                    nllMap[nllMapKey]=[]
                if nllMapKey[0]=='comb' and nllMapKey[1]==0:
                    nllMap[nllMapKey].append( allPdfs[key].createNLL(pseudoData, ROOT.RooFit.Extended()) )
                else:
                    nllMap[nllMapKey].append( nllMap[('comb',0)][-1] )

            if options.verbose>3:
                sys.stdout.write(' [running Minuit]')
                sys.stdout.flush()
            minuit=ROOT.RooMinuit(nllMap[('comb',0)][-1])
            minuit.setErrorLevel(0.5)
            minuit.migrad()
            minuit.hesse()
            minuit.minos(poi)

            #save fit results
            summary.addFitResult(key=key,ws=ws)

            #show, if required
            selstring = options.selection if options.selection else 'inclusive'
            if options.spy and i==0:
                pll=nllMap[('comb',0)][-1].createProfile(poi)
                showFinalFitResult(data=pseudoData,pdf=allPdfs[key], nll=[pll,nllMap[('comb',0)][-1]],
                                   SVLMass=ws.var('SVLMass'),mtop=ws.var('mtop'),
                                   outDir=options.outDir,
                                   tag=[selstring,
                                   "%s channel, =%s tracks"%(
                                     str(chsel.split('_',1)[0]),
                                     str(trk))])
                #raw_input('press key to continue...')

            #save to erase later
            if pseudoDataH : allPseudoDataH.append(pseudoDataH)
            allPseudoData.append(pseudoData)
            if options.verbose>3:
                sys.stdout.write('%s DONE %s'
                                 '(mt: %6.2f+-%4.2f GeV, '
                                  'mu: %4.2f+-%4.2f)\n'%
                                (bcolors.OKGREEN,bcolors.ENDC,
                                 ws.var('mtop').getVal(), ws.var('mtop').getError(),
                                 ws.var('mu').getVal(), ws.var('mu').getError()) )
                sys.stdout.flush()

        #combined likelihoods
        if options.verbose>3:
            sys.stdout.write(prepend+'[combining channels and categories]')
            sys.stdout.flush()
        for key in nllMap:

            #reset to central values
            ws.var('mtop').setVal(172.5)
            ws.var('mu').setVal(1.0)

            #add the log likelihoods and minimize
            llSet = ROOT.RooArgSet()
            for ll in nllMap[key]: llSet.add(ll)
            combll = ROOT.RooAddition("combll","combll",llSet)
            minuit=ROOT.RooMinuit(combll)
            minuit.setErrorLevel(0.5)
            minuit.migrad()
            minuit.hesse()
            minuit.minos(poi)
            summary.addFitResult(key=key,ws=ws)
            combll.Delete()

            if options.verbose>3:
                print key,len(nllMap[key]),' likelihoods to combine'
                sys.stdout.write(' %s%s DONE%s%s '
                                 '(mt: %6.2f+-%4.2f GeV, '
                                 'mu: %5.3f+-%5.3f)%s \n'%
                                 (bcolors.OKGREEN, bcolors.BOLD, bcolors.ENDC, bcolors.BOLD,
                                  ws.var('mtop').getVal(), ws.var('mtop').getError(),
                                  ws.var('mu').getVal(), ws.var('mu').getError(),
                                  bcolors.ENDC))
                sys.stdout.flush()
                print 80*'-'

        #free used memory
        for h in allPseudoDataH      : h.Delete()
        for d in allPseudoData       : d.Delete()
        for ll in nllMap[('comb',0)] : ll.Delete()

    summary.saveResults()



def submitBatchJobs(wsfile, pefile, experimentTags, options, queue='8nh'):
    import time
    cmsswBase = os.environ['CMSSW_BASE']
    sel=''
    #EDIT
    #sel=options.selection
    if len(sel)==0 : sel='inclusive'
    baseJobsDir='svlPEJobs'
    if options.calib : baseJobsDir+='_calib'
    jobsDir = osp.join(cmsswBase,'src/UserCode/TopMassSecVtx/%s/%s'%(baseJobsDir,sel),time.strftime('%b%d'))
    if not osp.exists(jobsDir):
        os.system('mkdir -p %s'%jobsDir)

    print 'Single job scripts stored in %s' % jobsDir

    wsfilepath = osp.abspath(wsfile)
    pefilepath = osp.abspath(pefile)
    odirpath = osp.abspath(jobsDir)
    if options.calib:
        odirpath = osp.abspath(osp.join(jobsDir,'calibrated'))
        os.system('mkdir -p %s'%odirpath)

    ## Feedback before submitting the jobs
    if not options.noninteractive:
        raw_input('This will submit %d jobs to batch. %s '
                  'Did you remember to run scram b?%s \n '
                  'Continue?'%(len(experimentTags), bcolors.RED, bcolors.ENDC))

    for n,tag in enumerate(experimentTags):
        sys.stdout.write(' ... processing job %2d - %-22s' % (n+1, tag))
        sys.stdout.flush()
        scriptFileN = '%s/runSVLPE_%s.sh'%(jobsDir,tag)
        scriptFile = open(scriptFileN, 'w')
        scriptFile.write('#!/bin/bash\n')
        scriptFile.write('cd %s/src\n'%cmsswBase)
        scriptFile.write('eval `scram r -sh`\n')
        scriptFile.write('cd %s\n'%jobsDir)
        command = ('runSVLPseudoExperiments.py %s %s -o %s -v 3 %s -n %d' %
                      (wsfilepath, pefilepath, odirpath, tag, options.nPexp))
        #EDIT
        #if options.genFromPDF:
        #    command += ' --genFromPDF'
        if options.calib:
            command += ' --calib %s' % osp.abspath(options.calib)
        #EDIT
        #if len(options.selection):
        #    command += ' --selection %s'%options.selection
        scriptFile.write('%s\n'%command)
        scriptFile.close()
        os.system('chmod u+rwx %s'%scriptFileN)
        os.system("bsub -q %s -J SVLPE%d \'%s\'"% (queue, n+1, scriptFileN))
        sys.stdout.write(bcolors.OKGREEN+' SUBMITTED' + bcolors.ENDC)
    return 0

"""
steer
"""
def main():
    usage = """
    Run a set of PEs on a single variation:
    usage: %prog [options] SVLWorkspace.root pe_inputs.root nominal_172v5
    Run all PEs on batch
           %prog [options] SVLWorkspace.root pe_inputs.root
    """
    parser = optparse.OptionParser(usage)
    parser.add_option('--isData', dest='isData', default=False, action='store_true',
                       help='if true, final fit is performed')
    parser.add_option('--genFromPDF', dest='genFromPDF', default=False, action='store_true',
                       help='if true, pseudo-experiments are thrown thrown from the PDF')
    parser.add_option('--spy', dest='spy', default=False, action='store_true',
                       help='if true,shows fit results on the screen')
    parser.add_option('--noninteractive', dest='noninteractive', default=False,
                       action='store_true',
                       help='do not ask for confirmation before submitting jobs')
    parser.add_option('-v', '--verbose', dest='verbose', default=0, type=int,
                       help='Verbose mode')
    parser.add_option('-s', '--selection', dest='selection', default='',
                       help='selection type')
    parser.add_option('-c', '--calib', dest='calib', default='',
                       help='calibration file')
    parser.add_option('-f', '--filter', dest='filter', default='',
                       help='Run only on these variations (comma separated list)')
    parser.add_option('-n', '--nPexp', dest='nPexp', default=250, type=int,
                       help='Total # pseudo-experiments.')
    parser.add_option('-o', '--outDir', dest='outDir', default='svlfits',
                       help='Output directory [default: %default]')

    (opt, args) = parser.parse_args()

    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(0)
    ROOT.gROOT.SetBatch(True)
    #if opt.spy : ROOT.gROOT.SetBatch(False)
    ROOT.gSystem.Load("libUserCodeTopMassSecVtx")
    ROOT.AutoLibraryLoader.enable()
    if not opt.verbose > 5:
        ROOT.shushRooFit()
    # see TError.h - gamma function prints lots of errors when scanning
    ROOT.gROOT.ProcessLine("gErrorIgnoreLevel=kFatal")

    print 'Storing output in %s' % opt.outDir
    os.system('mkdir -p %s' % opt.outDir)
    os.system('mkdir -p %s' % osp.join(opt.outDir, 'plots'))

    # launch pseudo-experiments
    if not opt.isData:
        try:
            peInputFile = ROOT.TFile.Open(args[1], 'READ')
        except TypeError: ## this sometimes fails (too many accesses to this file?)
            import time
            time.sleep(5)
            peInputFile = ROOT.TFile.Open(args[1], 'READ')

        allTags = [tkey.GetName() for tkey in peInputFile.GetListOfKeys()]
        peInputFile.Close()
        print 'Running pseudo-experiments using PDFs and signal expectations'

        ## Run a single experiment
        if len(args)>2:
            if not args[2] in allTags:
                print ("ERROR: variation not "
                       "found in input file! Aborting")
                return -2

            ## Only run one PE for spy option
            if opt.spy:
                opt.nPexp = 1

            runPseudoExperiments(wsfile=args[0], pefile=args[1],
                                 experimentTag=args[2],
                                 options=opt)
            return 0

        #loop over the required number of jobs
        print 'Submitting PE jobs to batch'
        if len(opt.filter)>0:
            filteredTags = opt.filter.split(',')
            for tag in filteredTags:
                if not tag in allTags:
                    print ("ERROR: variation not "
                           "found in input file! Aborting")
                    return -3
            allTags = filteredTags
        submitBatchJobs(args[0], args[1], allTags, opt)

        return 0
    else:
        print 'Ready to unblind?'
        print '...ah ah this is not even implemented'
        return -1
    print 80*'-'
    return 0



if __name__ == "__main__":
    sys.exit(main())
