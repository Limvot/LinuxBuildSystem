#build.py
import os, subprocess

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


#This function loads the build steps from a file
def loadBuildSteps(build_steps_file):
	pass

#This function completes one step, usually an unpack, build and install.
def buildStep(build_step, build_dir):
	old_wd = os.cwd()
	#Extract
	os.chdir(build_dir + os.sep + "sources")
	extracted_dir = 

	#Change dir
	os.chdir(extracted_dir)

	#Follow build instructions

	#change back to sources directory
	os.chdir(build_dir + os.sep + "sources")

	#delete the extracted source directory and any build directories
	subprocess.call(["rm", "-rf", extracted_dir, "*-build"], shell=True)

	#return to regular working directory
	os.chdir(old_wd)

#This is the main function that loops through the steps
def buildSystem():
	print("Welcome to the LinuxFromScratch LinuxBuildSystem")

	#Load the configuration file into a dictionary
	config_file = open("LinuxBuildSystem.config", "r")
	config_lines = config_file.readlines()
	config_file.close()
	config = {}

	for line in config_lines:
		pair = line.split("=")
		config[pair[0]] = pair[1]

	print("Loaded LinuxBuildSystem.config")

	#Extract the download list from copypast book text, if needed
	extractDownloadList("downloadListUnprocessed.txt", "downloadlist.txt")

	#Download the sources to the source directory inside the path specified by the configuration file
	print(config["BUILD_DIR"] + os.sep + "sources")
	downloadSources(config["BUILD_DIR"] + os.sep + "sources", "downloadlist.txt")

	build_steps = loadBuildSteps()
	for build_step in build_steps:
		buildStep(build_step, config["BUILD_DIR"])



buildSystem()

