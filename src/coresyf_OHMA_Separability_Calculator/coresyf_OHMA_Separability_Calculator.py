"""
Python script to :
1) open an excel workbook (containing the cluster signature data)
2) extract the tabular information contained in the workbook sheets as arrays for onward use, iterating through the sheets.
3) close the workbook

The original code developed for desktop deployment is adapted here for integrating it into the Co-ReSyF platform, as part of a suite of files for operating on the platform.

Created by Rory Scarrott (13th August 2018), UCC Department of Geography, ERI, August 2018 as part of work under the H2020-CoReSyF initiatives Research Applications work package.

Version 1.0.2
"""

__author__ = "Rory Scarrott"
__version__ = "1.0.2"
__copyright__ = "Copyright 2018, University College Cork"

# 1) Preliminaries - import some libraries

# enables the numpy suite of tools to access, process and analyse arrays of data
import numpy as np
# enables one to query file structures (e.g. seeing if a file is empty)
import os
# enables a high-performance, easy-to-use data structures and suite of data analysis tools
import pandas as pd
import xlrd			# to open an excel spreadsheet and access the data held within.
import math
# enables the suite of Co-ReSyF tools to be used allowing this script to be run on hugh volumes of data.
from coresyftools.tool import CoReSyFTool

# 2) Define the set of calculation functions.


def implementAnalysis(infilePathName, workbook):
    """ 
    Script to open the designated workbook and implement the analyses. 
    This script uses xlrd and pandas functions to open the .xlxs file, and extract the required structural information to run the data extraction scripts. It then initiates the implementation of the suite of analysis functions.

    It's only parameter input is the designated files path and filename. 
    """
    sheetBreakdown = workbook.sheet_names()
    sheet_number = len(sheetBreakdown)
    xl = pd.ExcelFile(infilePathName)
    df = xl.sheet_names
    nClusterSep = calculateSeparabilities(df, workbook)

    return nClusterSep


def calculateSeparabilities(df, workbook):
    """calculates separability measures from an Excel Workbook, and saves them in a dictionary which the function returns. 

    This script iterates through a list of class outputs held on worksheets in a single microsoft workbook, comparing each cluster (sheet) to the others in the workbook. Using customised component functions, it calculates the Jeffries Mathusita Index, and the Divergence measure of separability (using the formula outlined in Swain and Davis, 1978) for each cluster pair, collates these as two lists. It then calculates the average of both measures, and determines the minimum value of both in the matrix of comparisons. 

    These summary measures, along with the produced lists are collated into a dictionary for returning and onward use. produced per input excel workbook.

    The function calls upon five custom fuctions as part of its operation: 
            gatherClusterInfo()
            calculateJeffriesMathusita()
            calculateDivergence()
            calculateMinAvgJM()
            calculateMinAvgDiv()

    Its input parameter required is df, which is a list of worksheet names, extracted from the workbook using pandas (a combination of the .Excel() and .sheet_names() methods).
    """

    listComparativesSep = []
    listJM = []
    listDiv = []
    # iterate through each sheet, comparing to all other sheets
    for i in range(0, len(df)):
        clusterIName = df[i]  # set a cluster name
        for j in range(0, len(df)):  # len(df)
            clusterJName = df[(j)]  # set a comparator cluster name
            k = (i+1, j+1)
            listComparativesSep.append(k)
            # gathers the calc data from sheets.
            clstrIJVars = gatherClusterInfo(clusterIName, clusterJName, workbook)
        # calculate the Jeffries Mathusita index for designated pairs
            JM = calculateJeffriesMathusita(
                clstrIJVars.get("meanCl_i"),
                clstrIJVars.get("meanCl_j"),
                clstrIJVars.get("coVarCl_i"),
                clstrIJVars.get("coVarCl_j")
            )
        # calculate the Divergence for designated pairs
            Div = calculateDivergence(
                clstrIJVars.get("meanCl_i"),
                clstrIJVars.get("meanCl_j"),
                clstrIJVars.get("coVarCl_i"),
                clstrIJVars.get("coVarCl_j"))
            listJM.append(JM)
            listDiv.append(Div)

        # Calculate the average Jeffries-Mathusita, and extract the minimum Jeffries Mathusita value from the calculateJeffriesMathusita()- and calculateDivergence()-produced lists.
    MinAvgJM = calculateMinAvgJM(listJM)
    MinAvgDiv = calculateMinAvgDiv(listDiv)
    output = dict(MinAvgJM.items() + MinAvgDiv.items())
    # Append the dictionaries with ancilliary information
    output["n_ClustersSep"] = int(len(df))
    output["SepCompareList"] = listComparativesSep
    output["JMList"] = listJM
    output["DivList"] = listDiv
    return output


def gatherClusterInfo(clusterIName, clusterJName, workbook):
    """Gather covariance matrices & mean vectors for the separability calculation
    This function accesses the excel workbook containing the covariance matrices and mean vector data for two clusters being compared, extracts these variables and stores them as arrays. It then produces a dictionary containing each of the variables, with the variable names as keys. """

    # figure out each sheets dimensions
    worksheeti = workbook.sheet_by_name(clusterIName)
    worksheetj = workbook.sheet_by_name(clusterJName)
    num_rowsi = worksheeti.nrows - 1
    num_rowsj = worksheetj.nrows - 1
    num_colsi = worksheeti.ncols
    num_colsj = worksheetj.ncols

    # get the 4 sets of tabular data as 4 arrays
    # extract coVarCl_j
    coVarCl_i = np.asarray([[worksheeti.cell_value(r, c) for c in range(5, num_colsi)] for r in range(
        1, (num_rowsi+1))])  # extracts a table from cell (5,2) to (x,y), and stores it as a numpy array
    # extract meanCl_i
    meanCl_i = np.asarray([[worksheeti.cell_value(r, c) for c in range(3, 4)] for r in range(
        1, num_rowsi+1)])  # clusterIName within workbook, column 4, rows 2 to length of column 4
    # extract coVarCl_j
    coVarCl_j = np.asarray([[worksheetj.cell_value(r, c) for c in range(
        5, num_colsj)] for r in range(1, (num_rowsj+1))])
    # extract meanCl_j
    meanCl_j = np.asarray([[worksheetj.cell_value(r, c) for c in range(3, 4)] for r in range(
        1, num_rowsj+1)])  # clusterIName within workbook, column 4, rows 2 to length of column 4

    # store the arrays in a dictionary and return this dictionary
    clstrIJVars = {"coVarCl_i": coVarCl_i, "meanCl_i": meanCl_i,
                   "coVarCl_j": coVarCl_j, "meanCl_j": meanCl_j}
    return clstrIJVars


def calculateJeffriesMathusita(meanCl_i, meanCl_j, coVarCl_i, coVarCl_j):
    """Calculates the Jeffries-Mathusita index measurement of separability 
    Calculates the J-M measure of separability between two cluster pairs (cluster i, and cluster j), with the input data consisting of the mean vector matrix of cluster 1, mean vector matrix of cluster j, covariance matrix of cluster i, and the covariance matrix of cluster j."""

    # get meanDiffCli&j = (meanCl_i - meanCl_j)
    meanDiffCliandj = meanCl_i - meanCl_j
    # get meadDiffTCli&j = the transpose of (meanCl_i - meanCl-j)
    meanDiffTCliandj = meanDiffCliandj.transpose()
    # get detCoVarCli = the determinant of coVarCl_i
    detCoVarCli = np.linalg.det(coVarCl_i)
    # get detCoVarClj = the determinant of coVarCl_j
    detCoVarClj = np.linalg.det(coVarCl_j)
    # get sumIandJ = the sum of coVarCl_i and coVarCl_j
    sumIandJ = coVarCl_i + coVarCl_j
    # Get invHalfSumIandJ
    invHalfSumIandJ = np.linalg.inv((sumIandJ/2))
    # Get the determinant of half of the sum of the covariance matrices i and j
    detHalfSumIandJ = np.linalg.det((sumIandJ/2))
    # Bring it all together to get matrix A and Matrix B for Alpha = MatrixA/8 + (Ln(MatrixB))/2
    matrixA = (
        np.matmul((np.matmul(meanDiffTCliandj, invHalfSumIandJ)), meanDiffCliandj))/8
    matrixB = math.log((detHalfSumIandJ) /
                       (math.sqrt(detCoVarCli * detCoVarClj))) / 2
    alpha = matrixA + matrixB
    # Calculate JMx1000 and remove anything after the decimel point
    JM = int(round((1000*(math.sqrt(2*(1 - (math.exp(-alpha)))))), 0))

    return JM


def calculateDivergence(meanCl_i, meanCl_j, coVarCl_i, coVarCl_j):
    """Calculates the Divergence index measurement of separability 
    Calculates the Divergence measure of separability between two cluster pairs (cluster i, and cluster j), with the input data consisting of....."""

    # get invCoVarCl_i = the inverse of CoVarCl_i
    invCoVarCl_i = np.linalg.inv(coVarCl_i)
    # get invCoVarCl_j = the inverse of CoVarCl_j
    invCoVarCl_j = np.linalg.inv(coVarCl_j)
    # get diffCoVarIandJ = the difference between CoVarCl_i and CoVarCl_j
    diffCoVarIandJ = coVarCl_i - coVarCl_j
    # get diffInvCoVarJandI = the difference between the inverse of CoVar j and the inv, Covar i
    diffInvCoVarJandI = invCoVarCl_j - invCoVarCl_i
    # get meanDiffCli&j = (meanCl_i - meanCl_j)
    diffMeanCliandj = meanCl_i - meanCl_j
    # get meanDiffTCli&j = the transpose of (meanCl_i - meanCl-j)
    diffMeanTCliandj = np.transpose(diffMeanCliandj)
    # get sumInvCovarIandInvCoVarJ = the sum of the inverse of coVarCl_i and the inv. of coVarCl_j
    sumInvCovarIandInvCoVarJ = invCoVarCl_i + invCoVarCl_j

    # Bring it all together to get the traces of matrix A and Matrix B and apply Div = 0.5tr(MatrixA) + 0.5*tr(MatrixB)
    matrixA = np.matmul(diffCoVarIandJ, diffInvCoVarJandI)
    matrixB = np.matmul(sumInvCovarIandInvCoVarJ,
                        (np.matmul(diffMeanCliandj, diffMeanTCliandj)))
    Div = int(round((0.5 * np.trace(matrixA)) + (0.5 * np.trace(matrixB))))

    return Div


def calculateMinAvgJM(listJM):
    """Extracts the Average and Minimum Jeffries-Mathusita values.
    The script runs through a 1-D array of pairwise separability (Jeffries Mathusita) caluclations between classes, and first removes all the zeros. It then identifies and extracts the minimum value from the 1-D array, before calculating the average of all the values in the list (minus the zeros). The script then outputs the two values as a dictionary with Min_JM, and Avg_JM as the keys"""

    listJMlessZero = [x for x in listJM if x != 0] 	# removes the zeros
    Min_JM = min(listJMlessZero)					# get minimum value
    Avg_JM = int(round(np.mean(listJMlessZero)))  # get the average value
    # store the two values in a returnable dictionary
    output = {"Min_JM": Min_JM, "Avg_JM": Avg_JM}
    return output


def calculateMinAvgDiv(listDiv):
    """Extracts the Minimum and Average Divergence values.
    The script runs through a 1-D array of pairwise separability (Divergence) caluclations between classes, and first removes all the zeros. It then identifies and extracts the minimum value 	from the 1-D array, before calculating the average of all the values in the list (minus the zeros). The script then outputs the two values as a dictionary with Min_Div, and Avg_Div as the keys"""

    listDivlessZero = [x for x in listDiv if x != 0] 	# removes the zeros
    Min_Div = min(listDivlessZero)						# get minimum value
    Avg_Div = int(round(np.mean(listDivlessZero)))		# get the average value
    # store the two values in a returnable dictionary
    output = {"Min_Div": Min_Div, "Avg_Div": Avg_Div}
    return output


def writeOutputDetailsToTxt(outfilePathName2, nClusterSep):
    """
    Writes the analysis outputs of a single .xlxs file analysis to a textfile 

    Writes the value contained in each key of the nClusterSep dictionary into the output text file line by line, preceded by a piece of explanatory text.

    "os.linesep" moves the writing to the next line
    """

    my_file = open(outfilePathName2, "w")
    my_file.write("Number of Clusters" + os.linesep)
    my_file.write(str(nClusterSep.get("n_ClustersSep")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("Average Divergence" + os.linesep)
    my_file.write(str(nClusterSep.get("Avg_Div")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("Minimum Divergence" + os.linesep)
    my_file.write(str(nClusterSep.get("Min_Div")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("Average Jeffries Mathusita" + os.linesep)
    my_file.write(str(nClusterSep.get("Avg_JM")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("Minimum Jeffries Mathusita" + os.linesep)
    my_file.write(str(nClusterSep.get("Min_JM")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("Pairwise comparative details" + os.linesep)
    my_file.write(
        "List of cluster pairs analysed for separability" + os.linesep)
    my_file.write(str(nClusterSep.get("SepCompareList")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("List of calculated JM values" + os.linesep)
    my_file.write(str(nClusterSep.get("JMList")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.write("List of calculated Div values" + os.linesep)
    my_file.write(str(nClusterSep.get("DivList")) + os.linesep)
    my_file.write("" + os.linesep)
    my_file.close()


def writeAvgMinOutputToTxt(outfilePathName1, finalOutput):
    """
    Writes finalOutput into an easily understandable textfile.

    Writes the finalOutput dictionary into the output text file line by line. 
    os.linesep moves the writing to the next line
    the script accesses the finalOutput dictionary, extracts the key values (which are lists), converts the list to a string, then edits the string to remove "[" and "]", whilst replacing the "," with a tab space."
    """

    my_file = open(outfilePathName1, "w")
    my_file.write("Number of Clusters" + os.linesep)  # linesep - go 2 nxt lne
    my_file.write(((((str(finalOutput["n_ClustersSep"])).replace(
        "[", "")).replace(",", "\t").replace("]", "")) + os.linesep))
    my_file.write("" + os.linesep)
    my_file.write("Average Divergence" + os.linesep)
    my_file.write(((((str(finalOutput["Avg_Div"])).replace(
        "[", "")).replace(",", "\t").replace("]", "")) + os.linesep))
    my_file.write("" + os.linesep)
    my_file.write("Minimum Divergence" + os.linesep)
    my_file.write(((((str(finalOutput["Min_Div"])).replace(
        "[", "")).replace(",", "\t").replace("]", "")) + os.linesep))
    my_file.write("" + os.linesep)
    my_file.write("Average Jeffries Mathusita" + os.linesep)
    my_file.write(((((str(finalOutput["Avg_JM"])).replace(
        "[", "")).replace(",", "\t").replace("]", "")) + os.linesep))
    my_file.write("" + os.linesep)
    my_file.write("Minimum Jeffries Mathusita" + os.linesep)
    my_file.write(((((str(finalOutput["Min_JM"])).replace(
        "[", "")).replace(",", "\t").replace("]", "")) + os.linesep))
    my_file.write("" + os.linesep)
    my_file.close()


# REVIEW and REVISE the BELOW

# Section 3) The implementation part of the tool when it's up and running on the system
#  i)  CoReSyFTool class, contains all those lovely functions which enable the tool to operate within the Co-ReSyF system (e.g. accessing the datasets in the cloud, appearing as a discrete tool in the workflow manager etc.)... all those things that someone has done to enable you to run your tool on the platform. Section 3 is an addition to your code to make your tool take on all these wonderful bits and use them (inherit).
# ii) The CoresyfOHMASeparabilityDecision(CoReSyFTool) then contains a "Run method", which basically tells the system to implement the sequence of procedures/functions (opening files, checking the separability peaks and plateaus, making the decisions etc.), so all implementation codelines get put into the CoresyfOHMASeparabilityDecision(CoReSyFTool) class

class CoresyfOHMASeparabilityCalculator(CoReSyFTool):
    """Contains the instructions to run all the functions contained in the Separability Calculator tool, supported by methods and functions described in the CoReSyFTool class."""

    def run(self, bindings):  # this is a Method - n.b. "self" can stay as is, "bindings" does not need to be defined in your code

        infile_path = bindings["Ssource"]  # sets the input file
        outfile_path = bindings["Ttarget"]  # sets the output file
        if not os.path.exists(outfile_path):
            os.makedirs(outfile_path)
        # TODO: change to logging module
        print("Open file from {}.".format(infile_path))

        finalOutput = {
                "n_ClustersSep": [],
                "Avg_JM": [],
                "Min_Div": [],
                "Avg_Div": [],
                "Min_JM": []
            }

        outfileName1 = "2011_SeparabilityOutputs.txt"
        outfilePathName1 = os.path.join(outfile_path, outfileName1)
        outfileName2 = "2011_SeparabilityOutputsDetails.txt"
        outfilePathName2 = os.path.join(outfile_path, outfileName2)

        for infileName in os.listdir(infile_path):
            if infileName.endswith(".xlsx"):
                infilePathName = os.path.join(infile_path, infileName)
                workbook = xlrd.open_workbook(infilePathName, on_demand=True)
                nClusterSep = implementAnalysis(infilePathName, workbook)
                writeOutputDetailsToTxt(outfilePathName2, nClusterSep)

                finalOutput["n_ClustersSep"].append(
                    nClusterSep["n_ClustersSep"])
                finalOutput["Min_Div"].append(nClusterSep["Min_Div"])
                finalOutput["Avg_Div"].append(nClusterSep["Avg_Div"])
                finalOutput["Min_JM"].append(nClusterSep["Min_JM"])
                finalOutput["Avg_JM"].append(nClusterSep["Avg_JM"])
            else:
                print("No more files to analyse")

            writeAvgMinOutputToTxt(outfilePathName1, finalOutput)

            print("Separability Calculation Completed")
