#build.py
import os, subprocess, copy, sys
from package import * #Our package 

#This function takes a txt file grabbed from the LFS book and converts it into a list of files to download
def extractDownloadList(input_file_path, output_file_path):
	input_file = open(input_file_path, "r")
	input_file_lines = input_file.readlines()
	input_file.close()

	extracted_lines = ""
	for line in input_file_lines:
		if "Download" in line:
			extracted_lines += (line.split(" "))[-1]

	output_file = open(output_file_path, "w")
	output_file.write(extracted_lines)
	output_file.close()


#This function downloads the sources needed, cacheing them in $BUILD_ROOT/sources
#Uses wget
def downloadSources(source_dir, download_list):
	old_wd = os.getcwd()	#Save working directory

	files_to_download = checkSources(source_dir, download_list)

	os.chdir(source_dir)

	for file_to_download in files_to_download:
		download_path = file_to_download[1][:-1] #Remove last char, which is line feed
		print(download_path)
		subprocess.call(["wget", download_path])

	os.chdir(old_wd)	#Return to previous working directory

	missing_list = checkSources(source_dir, download_list)
	for missing_file in missing_list:
		print("Missing", missing_file[0], "from", missing_file[1])

def checkSources(source_dir, download_list):
	old_wd = os.getcwd()	#Save working directory

	download_file = open(download_list, "r")
	download_filepaths = download_file.readlines()
	download_file.close()

	os.chdir(source_dir)	#Move to source_dir

	out_list = [] #Will be a list of tupels of file name an dpath name

	dirfiles = os.listdir()
	for download_path in download_filepaths:
		filename = (download_path[:-1]).split("/")[-1]
		if not filename in dirfiles:
			out_list.append( (filename, download_path) )

	os.chdir(old_wd)		#Restore working directory

	return(out_list)

def loadPackages(package_directory):

	#a dictonary of all the packages
	package_dictionary = {}
	#list the packages in the directory
	package_file_list = os.listdir(package_directory)

	for package_file in package_file_list:
		package = Package(package_directory + os.sep + package_file)

		for provided in package.properties["PROVIDES"]:
			package_dictionary[provided] = package

	return(package_dictionary)

def loadInstalledPackages(installed_package_file_path):

	#a dictonary of all the packages
	installed_package_file = open(installed_package_file_path, "r")
	installed_package_string = installed_package_file.read()
	installed_package_file.close()

	installed_package_dict = {}
	for installed_package in installed_package_string.split():
		installed_package_dict[installed_package] = "True"
	
	return(installed_package_dict)

def saveInstalledPackages(installed_package_dict, installed_package_file_path):

	#a dictonary of all the packages
	installed_package_file = open(installed_package_file_path, "w")
	installed_package_string = " ".join(installed_package_dict.keys())
	installed_package_file.write(installed_package_string)
	installed_package_file.close()



#This is the main function that loops through the steps
def buildSystem():
	print("Welcome to the LinuxBuildSystem!")

	#Find the base dir of where this script was called from
	base_dir = "/".join(os.path.abspath( __file__ ).split("/")[:-1])
	print(base_dir)

	config = {}

	script_string = ""

	#Load packages
	packages = loadPackages(base_dir+os.sep+"packages")

	#load installed packages
	installed_package_file_path = base_dir+os.sep+"installed_packages.txt"
	installed_packages = loadInstalledPackages(installed_package_file_path)

	#Lets look at our args. If -l or --list, print out the steps. Otherwise, use the params to gen the script, if correct number.
	print(sys.argv)
	if len(sys.argv) == 2:
		if sys.argv[1] == "-l" or sys.argv[1] == "--list":
			#Print out list of packages
			#First, assemble a list of packages, throwing out duplacates that arrise because a package provides more than one thing
			nodup_package_list = []
			for poss_dup_package in packages.values():
				if not poss_dup_package in nodup_package_list:
					nodup_package_list.append(poss_dup_package)

			package_print_string = ""
			for current_package in nodup_package_list:
				package_print_string += current_package.properties.get("NAME", "No_Name")
				package_print_string += " -- " + " ".join(current_package.properties.get("PROVIDES", "Provides_Nothing"))
				if " ".join(current_package.properties["PROVIDES"]) in installed_packages:
					package_print_string += " -- installed"
				package_print_string += "\n"
			print(package_print_string)
			return()


	#elif len(sys.argv) == 3 and (sys.argv[1] == "--download-sources" or sys.argv[1] == "-d"):

	elif not len(sys.argv) == 6:
		print("Welcome to the LinuxBuildSystem!")
		print("To list packages, call with -l or --list")
		print("To create a build script, call with <package> <start-step> <end-step> <base-build-dir> <output-script-file>")
		return()

	#Do input args
	package_name = sys.argv[1]
	begin_step = int(sys.argv[2])
	end_step = int(sys.argv[3])
	config["BUILD_DIR"] = sys.argv[4]	#Base dir
	script_output_dir = sys.argv[5]
	
	#get the package
	package = packages.get(package_name, "No Package")
	if package == "No Package":
		print("No package named", package_name)
		print("You can list all the packages available by calling this program with only -l or --list")
		return()

	#build the package
	script_string += "#!/bin/bash\nLBS_PROGRAM=" + os.path.abspath( __file__ ) + "\nLBS_BUILD_ROOT="+config["BUILD_DIR"]+"\n"
	script_string += package.build(begin_step, end_step, config, installed_packages, packages)
	saveInstalledPackages(installed_packages, installed_package_file_path)

	script_file = open(script_output_dir, "w")
	script_file.write(script_string)
	script_file.close()

	subprocess.call(["chmod 755 " + script_output_dir], shell=True)
	#subprocess.call("bash " + config["SCRIPT_FILE"], shell=True)



buildSystem()

