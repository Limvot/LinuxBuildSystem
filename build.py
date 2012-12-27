#build.py
import os, subprocess, copy

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
def loadBuildSteps(build_steps_file, config):
	step_file = open(build_steps_file, "r")

	build_steps = []
	build_step = []
	build_step.append({}) #0 index is a dictionary of config
	build_step.append([]) #1 index is a list of build commands

	line = step_file.readline()
	while not line == "":
		if not (line[0] == "#" or line == ""):
			split_line = line.split("@=") #To allow equals signs in commands, use different here

			if split_line[0] == "EXTRACT_COMMAND":
				build_step[0]["EXTRACT_COMMAND"] = split_line[1]

			if split_line[0] == "EXTRACTED_DIR":
				build_step[0]["EXTRACTED_DIR"] = split_line[1]

			if split_line[0] == "BUILD_STEP":
				build_step[0]["BUILD_STEP"] = split_line[1]

			if split_line[0] == "CONFIGURE_COMMAND":
				build_step[1].append(split_line[1])

			if split_line[0] == "MAKE_COMMAND":
				build_step[1].append(split_line[1])

			if split_line[0] == "IF_X64":
				if config["X64"] == "True":
					build_step[1].append(split_line[1])

			if split_line[0] == "INSTALL_COMMAND":
				build_step[1].append(split_line[1])

			if (not line.split() == []) and (line.split()[0] == "SETUP_EXTERNAL_BUILD_DIRECTORY"):
				build_step[0]["EXTERNAL_BUILD_DIRECTORY"] = "True"
				external_build_dir = build_step[0]["BUILD_STEP"].split()[0] + "-build"
				build_step[0]["EXTERNAL_BUILD_DIRECTORY_LOCATION"] = external_build_dir
				build_step[1].append("mkdir -v ../" + external_build_dir +"\n")
				build_step[1].append("cd ../" + external_build_dir +"\n")

			if (not line.split() == []) and (line.split()[0] == "BEGIN_COMMAND_BLOCK"):		#Split to find first word
				line = step_file.readline()
				while not line.split()[0] == "END_COMMAND_BLOCK":	#Split to find first word
					print("appending line to command block")
					build_step[1].append(line)
					line = step_file.readline()

			if (not line.split() == []) and (line.split()[0] == "END_BUILD_STEP"):
				build_steps.append(copy.deepcopy(build_step))
				print(build_step)
				build_step = [{},[]]

		line = step_file.readline()

	return(build_steps)


def buildStep(build_step, build_config):
	script_string = ""
	build_dir = build_config["BUILD_DIR"].split("\n")[0]

	#Extract
	script_string += "cd " + build_dir + os.sep + "sources" + "\n"
	script_string += build_step[0]["EXTRACT_COMMAND"] + "\n"


	#Change dir
	extracted_dir = build_step[0]["EXTRACTED_DIR"].split("\n")[0]
	script_string += "cd " + extracted_dir + "\n"

	#Follow build instructions
	for step in build_step[1]:
		print("adding", step, "to build script")
		script_string += step# + "\n"

	#change back to sources directory
	script_string += "cd " + build_dir.split("\n")[0] + os.sep + "sources" + "\n"

	#delete the extracted source directory and any build directories
	script_string += "rm " + "-rf " + extracted_dir + "\n"
	if build_step[0].get("EXTERNAL_BUILD_DIRECTORY", "False") == "True":
		script_string += "rm " +  "-rf " + build_step[0]["EXTERNAL_BUILD_DIRECTORY_LOCATION"] + "\n"

	#return our script to the top
	return(script_string)


#This is the main function that loops through the steps
def buildSystem():
	print("Welcome to the LinuxFromScratch LinuxBuildSystem")

	begin_step = int(input("step number to begin on:")) - 1; #0 index
	end_step = int(input("step number to end on:")) #Not -1 because of how range works

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
	source_dir = config["BUILD_DIR"].split("\n")[0] + os.sep + "sources" #get the source dir, removing a linefeed from the root dir if necessary
	print(source_dir)
	downloadSources(source_dir, "downloadlist.txt")

	script_string = ""

	build_steps = loadBuildSteps("buildsteps.txt", config)
	for build_step_index in range(begin_step, end_step):
		script_string += "#################\n#################\n#################\n"
		script_string += buildStep(build_steps[build_step_index], config)

	script_file = open(config["SCRIPT_FILE"], "w")
	script_file.write(script_string)
	script_file.close()

	subprocess.call(["chmod 755 " + config["SCRIPT_FILE"]], shell=True)
	subprocess.call("bash " + config["SCRIPT_FILE"], shell=True)



buildSystem()

