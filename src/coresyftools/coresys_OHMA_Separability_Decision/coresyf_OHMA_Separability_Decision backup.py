"""
Python script to extract the average and minimum, divergence and Jeffries Mathusita separability values 
from a .txt file and analysing them to locate the number of clusters whereby 1) a plateau in both average 
and minimum JM is reached, and this plateau coincides with a concident peak in average and minimum 
divergence.

The resulting list of optimal numbers of clusters which summarise the variability in the data are then written back into a new 
original SeparabilityMeasuresDecision.txt file as a new line in a list form, followed by underpinning decision data. 
The 1st value on the second line of the SeparabilityMeasuresDecision textfileis the one for the algorithm to select for onward use.

Version 1.0 (18th July 2018) Created by Rory Scarrott, UCC Department of Geography, ERI, University College Cork, and Julius Schroeder (an Erasmus intern) as part of work under the H2020-CoReSyF initiative's Research Applications work package.
"""

#Section 1) Preliminaries - import some libraries, and set the filepath and filename of interest

import os

#Section 2) Define a set of functions to implement - for the upload to Co-ReSyF, sections 1 and 2 go in a specific .py file describing the functions the run file calls.

def get_sep_dict(in_file): 
    """Returns a dict containing keys which are the separability descriptions, and values."""
    sep_dict = {}
    for line in in_file:
        if len(line) > 1:
            if line[0].isalpha():
                key = line.rstrip("\t\n").replace(" ","_").lower()
                values = in_file.next().replace("\n",'').split("\t")
                sep_dict[key] = [int(i) for i in values]
    return sep_dict

# find local peaks

def find_local_Div_peaks(variable):
    """looks specifically at the two divergence summaries (average and minimum), 
    returning a dict containing 1s and 0s. 1 represents peak, 0 represents no peak"""
    peakDivDec = [] # working - if x at location l is greater than x at location l-1, and x at l is greater than x at location l+1, then output 1, else 0
    for position in range(0,len(variable)):
        if ((position-1) < 0) or ((position + 1) >= len(variable)): #if position lies at class 10 or class 100 - null n' void
            a = 0
        elif (variable[position-1] < variable[position]) and (variable[position+1] < variable[position]): # if it satisfies both conditions - i.e. it's a peak
            a = 1
        else:
            a = 0
        peakDivDec.append(a)
    return peakDivDec

def find_local_JM_plateau(variable):
    """looks specifically at the two Jeffries-Mathusita summaries (average and minimum), 
    returning a dict containing 1s and 0s. 1 represents = 1414, 0 represents not"""
    platJMDec = [] # working - if x = 1414, it will return a value of 1, if < 1414, it will return a value of 0
    for value in variable:
        if value == 1414:
            a = 1
        else:
            a = 0
        platJMDec.append(a)
    return platJMDec

def make_peak_plateau_decisions(variable): # variable is a dictionary of "{key1:[separability values], key2:[separability values]}"
    """Runs through the dictionary of separability values, identifying peaks in the 
    case of divergences, and identifying plateaus in JM""" 
    sepDec_dict = {}
    for key, value in sep_dict.iteritems():
        if key in ["average_divergence", "minimum_divergence"]:
            sepDec_dict[key] = find_local_Div_peaks(value)
        elif key in ["average_jeffries_mathusita", "minimum_jeffries_mathusita"]:
            sepDec_dict[key] = find_local_JM_plateau(value)
        else:
            print "ERROR: {} key variable unknown".format(key)
    return sepDec_dict

def locate_peaks_plateau(dictionary1, dictionary2):     #dictionary 1 contains a key:value pair on cluster numbers, dictionary 2 contains key:value pairs of all the peak/plateau decisions
    """Produces a list of decisions for each cluster output number, a value of 0 denotes either 
    no peak, or no plateau, whilst the cluster number (e.g. 15) denotes both divergence peaks and 
    both Jeffries Mathusita plateaus occuring in the output of cluster 15
    As an aside, it produces a logging file note consisting of a list of integers where 0 
    represents no peak/plateau, and the cluster number (>0) represents the cluster output 
    where a peak/plateau coincide"""
    n_clusters = [a*b*c*d*e for a,b,c,d,e in zip(dictionary2["minimum_divergence"],
        dictionary2["average_divergence"],
        dictionary2["average_jeffries_mathusita"],
        dictionary2["minimum_jeffries_mathusita"],
        dictionary1["number_of_clusters"])]                         
    print n_clusters                       #  TODO: change to logging module  
    return n_clusters

def find_optimal_cluster(variable):
    """Selects and outputs the optimal number of clusters to represent dataset variability, which is the minimum number of clusters, where there is a peak in divergence measures, and a plateau in Jeffries Mathusita measures."""
    optimal_cluster = " "
    for value in n_clusters:
        if value > 0:
            optimal_cluster = int(value)
            break
    return optimal_cluster

def record_details(variable): # variable = output file, termed here as out_file
    out_file.writelines([
        "1) Optimal number of clusters" + "\n",
        str(opt_cluster) + "\n",
        "2) Cluster outputs with coincident divergence peaks and Jeffries-Mathusita plateaus (0 = no coincidence, >0 = cluster number at which coincidence occurs)" + "\n",
        str(n_clusters) + "\n",
        "3) Peak and Plateau decisions for each cluster output for each separability measure (min and average divergence, min and average Jeffries-Mathusita)" + "\n",
        str(sepDec_dict) + "\n",
        "4) Raw Separability values for each cluster output" + "\n",
        str(sep_dict)
        ])

#Section 3) Run the programme, calling the defined functions - these line go in the run function of the tool uploaded to Co-ReSyF

infile_dir = "C:\\PythonF\\00_PythonMusings\\20180502_SeparabilityAnalysis" # We will need to change this. 
infile_name = "2011_SeparabilityMeasures.txt"
infile_path = os.path.join(infile_dir, infile_name)

print("Open file from {}.".format(infile_path)) # TODO: change to logging module

in_file = open(infile_path)

sep_dict = get_sep_dict(in_file)

in_file.close()

sepDec_dict = make_peak_plateau_decisions(sep_dict)
n_clusters = locate_peaks_plateau(sep_dict, sepDec_dict)
opt_cluster = find_optimal_cluster(n_clusters)

print opt_cluster # This is the output

outfile_dir = "C:\\PythonF\\00_PythonMusings\\20180502_SeparabilityAnalysis" # We will need to change this. 
outfile_name = "SeparabilityMeasuresDecision.txt"
outfile_path = os.path.join(outfile_dir, outfile_name)
 
print("Open file from {}.".format(outfile_path)) # TODO: change to logging module

out_file = open(outfile_path,"a")
record_details(out_file)
out_file.close()