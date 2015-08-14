#! /usr/bin/env python
import ROOT

"""
Method to deal with the different versions of the histograms based on the leptons.
"""
def Get_Category(option):

    code_categories = []
    if option == 'e2j':
        code_categories = ['WW','WJets','TTWJets','SingleTbar_tW','DYJetsToLL_50toInf','TTJets_MSDecays_172v5','QCDPt80to170']
    elif option == 'e3j':
        code_categories = ['WW','WJets','TTWJets','SingleTbar_tW','DY1JetsToLL_50toInf','TTJets_MSDecays_172v5','QCDPt80to170']
    elif option == 'mu2j':
        code_categories = ['WW','WJets','TTWJets','SingleTbar_tW','DYJetsToLL_50toInf','TTJets_MSDecays_172v5','QCDPt80to170']
    else:
        code_categories = ['WW','WJets','TTWJets','SingleTbar_tW','DYJetsToLL_50toInf','TTJets_MSDecays_172v5','QCDPt250to350']

    return code_categories

"""
Calculate the sig/bkg with various cuts from the integrals of the histograms in plotter.root.

Particularly, we want to look at cuts that cut progressively higher (ie. 2.5<fjeta<5 -> 2.6<fjeta<5 -> 2.7<fjeta<5 -> etc.)

Inputs are: name (name of the cut you are looking at), bins: number of bins in the histogram, initial: starting value of the histogram, final: final value of the histogram

Also note: you need to change the rootfile to get the correct plot (need the directory).
"""
def Calculate_Cut_High(name,bins,initial,final):
    
    rootfile = ROOT.TFile.Open("/afs/cern.ch/user/e/edrueke/edrueke/top_lxy/CMSSW_5_3_22/src/UserCode/TopMassSecVtx/singleTop/plots_base_deltaeta_cut/plotter.root")

    outfile = open(name+'_calculations_high.txt','w')
    
    options = ['e2j','e3j','mu2j','mu3j']

    write_categories = ['Multiboson','W+Jets','Other ttbar','Single top','DY+Jets','ttbar','QCD Multijets']

    bn_ct = 1
    bn_width = (final-initial)/bins

    while bn_ct<bins:
        current_cut = str((bn_ct-1)*bn_width+initial)
        outfile.write(str((bn_ct-1)*bn_width+initial)+' < '+name+' < '+str(final)+'\n\n')
        for option in options:
            outfile.write(option+':\n')
            code_categories = Get_Category(option)
            sig_ct = 0
            bkg_ct = 0
            ttbar_ct = 0
            hist = ROOT.TH1F()
            i=0
            rootfile.cd(name+'_'+option)
            for cat in code_categories:
                
                ROOT.gDirectory.GetObject('MC8TeV_'+cat+'_'+name+'_'+option,hist)
                ct = hist.Integral(bn_ct,bins)
                #outfile.write(write_categories[i]+': '+str(ct)+'\n')
                if write_categories[i]=='Single top':
                    sig_ct+=ct
                elif write_categories[i]=='Other ttbar' or write_categories[i]=='ttbar':
                    ttbar_ct+=ct
                    bkg_ct+=ct
                else:
                    bkg_ct+=ct
                i+=1
            
            sig_bkg_ratio = 0
            sig_ttbar_ratio = 0

            if bkg_ct!=0:
                sig_bkg_ratio = sig_ct/bkg_ct
            else:
                sig_bkg_ratio = 1
            if ttbar_ct!=0:
                sig_ttbar_ratio = sig_ct/ttbar_ct
            else:
                sig_ttbar_ratio = 1

            if sig_bkg_ratio == 1: 
                continue
            
            outfile.write('\nsig: '+str(sig_ct)+'\n')
            outfile.write('bkg: '+str(bkg_ct)+'\n')
            outfile.write('ttbar: '+str(ttbar_ct)+'\n')
            outfile.write('\nsig/bkg: '+str(sig_bkg_ratio)+'\n')
            outfile.write('sig/ttbar: '+str(sig_ttbar_ratio)+'\n\n')
            
        outfile.write('\n######################################\n')
    
        bn_ct+=1
    
    outfile.close()

"""
Calculate the sig/bkg with various cuts from the integrals of the histograms in plotter.root.

Particularly, we want to look at cuts that cut progressively lower (ie. 2.5<fjeta<5 -> 2.5<fjeta<4.9 -> 2.5<fjeta<4.8 -> etc.)

Inputs are: name (name of the cut you are looking at), bins: number of bins in the histogram, initial: starting value of the histogram, final: final value of the histogram
"""
def Calculate_Cut_Low(name,bins,initial,final):
    
    rootfile = ROOT.TFile.Open("/afs/cern.ch/user/e/edrueke/edrueke/top_lxy/CMSSW_5_3_22/src/UserCode/TopMassSecVtx/singleTop/plots/plotter.root")

    outfile = open(name+'_calculations_low.txt','w')
    
    options = ['e2j','e3j','mu2j','mu3j']

    write_categories = ['Multiboson','W+Jets','Other ttbar','Single top','DY+Jets','ttbar','QCD Multijets']

    bn_ct = 2
    bn_width = (final-initial)/bins

    while bn_ct<bins:
        current_cut = str(initial+((bn_ct)*bn_width))
        outfile.write(str(initial)+' < '+name+' < '+current_cut+'\n\n')
        for option in options:
            outfile.write(option+':\n')
            code_categories = Get_Category(option)
            sig_ct = 0
            bkg_ct = 0
            ttbar_ct = 0
            hist = ROOT.TH1F()
            i=0
            rootfile.cd(name+'_'+option)
            for cat in code_categories:
                
                ROOT.gDirectory.GetObject('MC8TeV_'+cat+'_'+name+'_'+option,hist)
                ct = hist.Integral(1,bn_ct)
                #outfile.write(write_categories[i]+': '+str(ct)+'\n')
                if write_categories[i]=='Single top':
                    sig_ct+=ct
                elif write_categories[i]=='Other ttbar' or write_categories[i]=='ttbar':
                    ttbar_ct+=ct
                    bkg_ct+=ct
                else:
                    bkg_ct+=ct
                i+=1
            
            sig_bkg_ratio = 0
            sig_ttbar_ratio = 0

            if bkg_ct!=0:
                sig_bkg_ratio = sig_ct/bkg_ct
            else:
                sig_bkg_ratio = 1
            if ttbar_ct!=0:
                sig_ttbar_ratio = sig_ct/ttbar_ct
            else:
                sig_ttbar_ratio = 1

            if sig_bkg_ratio == 1:
                continue

            outfile.write('\nsig: '+str(sig_ct)+'\n')
            outfile.write('bkg: '+str(bkg_ct)+'\n')
            outfile.write('ttbar: '+str(ttbar_ct)+'\n')
            outfile.write('\nsig/bkg: '+str(sig_bkg_ratio)+'\n')
            outfile.write('sig/ttbar: '+str(sig_ttbar_ratio)+'\n\n')
                            
        outfile.write('\n######################################\n')
    
        bn_ct+=1
    
    outfile.close()

"""
Calculate the percentages of the correct, wrong, and unmatched bs
"""
def Calculate_Comb_Info():
    
    rootfile = ROOT.TFile.Open("/afs/cern.ch/user/e/edrueke/edrueke/top_lxy/CMSSW_5_3_22/src/UserCode/TopMassSecVtx/singleTop/plots_base/plotter.root")

    outfile = open('CombInfo_calculations.txt','w')
    
    options = ['e2j','mu2j']

    write_categories = ['Multiboson','W+Jets','Other ttbar','Single top','DY+Jets','ttbar','QCD Multijets']

    hist = ROOT.TH1F()

    sig_all_total=0
    sig_all_cor=0
    sig_all_wrong=0
    sig_all_unm=0
    ttbar_all_total=0
    ttbar_all_cor=0
    ttbar_all_wrong=0
    ttbar_all_unm=0
    bkg_all_total=0
    bkg_all_cor=0
    bkg_all_wrong=0
    bkg_all_unm=0

    for opt in options:
        rootfile.cd("CombInfo_"+opt)
        
        code_categories = Get_Category(opt)

        i = 0

        sig_opt_total=0
        sig_opt_cor=0
        sig_opt_wrong=0
        sig_opt_unm=0
        ttbar_opt_total=0
        ttbar_opt_cor=0
        ttbar_opt_wrong=0
        ttbar_opt_unm=0
        bkg_opt_total=0
        bkg_opt_cor=0
        bkg_opt_wrong=0
        bkg_opt_unm=0

        for cat in code_categories:
            ROOT.gDirectory.GetObject("MC8TeV_"+cat+"_CombInfo_"+opt,hist)

            total = hist.Integral()
            wrong = hist.GetBinContent(1)
            unmatched = hist.GetBinContent(2)
            correct = hist.GetBinContent(3)

            outfile.write(write_categories[i]+' '+opt)
            outfile.write('\n   total = '+str(total))
            outfile.write('\n   correct = '+str(correct)+' ('+str(100*correct/total)+'%)')
            outfile.write('\n   unmatched = '+str(unmatched)+' ('+str(100*unmatched/total)+'%)')
            outfile.write('\n   wrong = '+str(wrong)+' ('+str(100*wrong/total)+'%)'+'\n')
            
            if write_categories[i]=='Single top':
                sig_all_total+=total
                sig_opt_total+=total
                sig_all_wrong+=wrong
                sig_opt_wrong+=wrong
                sig_all_unm+=unmatched
                sig_opt_unm+=unmatched
                sig_all_cor+=correct
                sig_opt_cor+=correct
            elif write_categories[i] in ['Other ttbar','ttbar']:
                ttbar_all_total+=total
                ttbar_opt_total+=total
                ttbar_all_wrong+=wrong
                ttbar_opt_wrong+=wrong
                ttbar_all_unm+=unmatched
                ttbar_opt_unm+=unmatched
                ttbar_all_cor+=correct
                ttbar_opt_cor+=correct
                bkg_all_total+=total
                bkg_opt_total+=total
                bkg_all_wrong+=wrong
                bkg_opt_wrong+=wrong
                bkg_all_unm+=unmatched
                bkg_opt_unm+=unmatched
                bkg_all_cor+=correct
                bkg_opt_cor+=correct
            else:
                bkg_all_total+=total
                bkg_opt_total+=total
                bkg_all_wrong+=wrong
                bkg_opt_wrong+=wrong
                bkg_all_unm+=unmatched
                bkg_opt_unm+=unmatched
                bkg_all_cor+=correct
                bkg_opt_cor+=correct
                
            i+=1

        outfile.write(opt+' Totals: \n\n')
        outfile.write('    Signal:\n')
        outfile.write('          Correct = '+str(sig_opt_cor)+' ('+str(100*sig_opt_cor/sig_opt_total)+'%)\n')
        outfile.write('          Unmatched = '+str(sig_opt_unm)+' ('+str(100*sig_opt_unm/sig_opt_total)+'%)\n')
        outfile.write('          Wrong = '+str(sig_opt_wrong)+' ('+str(100*sig_opt_wrong/sig_opt_total)+'%)\n')
        outfile.write('    TTbar:\n')
        outfile.write('          Correct = '+str(ttbar_opt_cor)+' ('+str(100*ttbar_opt_cor/ttbar_opt_total)+'%)\n')
        outfile.write('          Unmatched = '+str(ttbar_opt_unm)+' ('+str(100*ttbar_opt_unm/ttbar_opt_total)+'%)\n')
        outfile.write('          Wrong = '+str(ttbar_opt_wrong)+' ('+str(100*ttbar_opt_wrong/ttbar_opt_total)+'%)\n')
        outfile.write('    Background:\n')
        outfile.write('          Correct = '+str(bkg_opt_cor)+' ('+str(100*bkg_opt_cor/bkg_opt_total)+'%)\n')
        outfile.write('          Unmatched = '+str(bkg_opt_unm)+' ('+str(100*bkg_opt_unm/bkg_opt_total)+'%)\n')
        outfile.write('          Wrong = '+str(bkg_opt_wrong)+' ('+str(100*bkg_opt_wrong/bkg_opt_total)+'%)\n')

    outfile.write('Overall  Totals: \n\n')
    outfile.write('    Signal:\n')
    outfile.write('          Correct = '+str(sig_all_cor)+' ('+str(100*sig_all_cor/sig_all_total)+'%)\n')
    outfile.write('          Unmatched = '+str(sig_all_unm)+' ('+str(100*sig_all_unm/sig_all_total)+'%)\n')
    outfile.write('          Wrong = '+str(sig_all_wrong)+' ('+str(100*sig_all_wrong/sig_all_total)+'%)\n')
    outfile.write('    TTbar:\n')
    outfile.write('          Correct = '+str(ttbar_all_cor)+' ('+str(100*ttbar_all_cor/ttbar_all_total)+'%)\n')
    outfile.write('          Unmatched = '+str(ttbar_all_unm)+' ('+str(100*ttbar_all_unm/ttbar_all_total)+'%)\n')
    outfile.write('          Wrong = '+str(ttbar_all_wrong)+' ('+str(100*ttbar_all_wrong/ttbar_all_total)+'%)\n')
    outfile.write('    Background:\n')
    outfile.write('          Correct = '+str(bkg_all_cor)+' ('+str(100*bkg_all_cor/bkg_all_total)+'%)\n')
    outfile.write('          Unmatched = '+str(bkg_all_unm)+' ('+str(100*bkg_all_unm/bkg_all_total)+'%)\n')
    outfile.write('          Wrong = '+str(bkg_all_wrong)+' ('+str(100*bkg_all_wrong/bkg_all_total)+'%)\n')
    

    outfile.close()

"""
Main Program
"""

def main():

    Calculate_Cut_High('FJEta',50,0.0,5.0)
#    Calculate_Cut_High('DeltaEtaJB',25,0.0,8.0)
#    Calculate_Cut_High('BDToutput',25,-0.4,0.45)

    #Calculate_Comb_Info()

main()
