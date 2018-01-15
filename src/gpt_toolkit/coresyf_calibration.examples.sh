#Nominal cases:

#simple_example
#Check example
coresyf_calibration --Ssource S1A_EW_GRDM_1SDH_20171001T060648_20171001T060753_018615_01F62E_EE7F --Ttarget result

#complex_example
#Test complex example
coresyf_calibration --Ssource S1A_EW_GRDM_1SDH_20171001T060648_20171001T060753_018615_01F62E_EE7F --Ttarget result --PauxFile 'Latest Auxiliary File' --PcreateBetaBand true --PcreateGammaBand true --PoutputBetaBand true --PoutputGammaBand true --PoutputImageInComplex true --PoutputImageScaleInDb true --PoutputSigmaBand true