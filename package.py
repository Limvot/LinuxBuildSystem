#package.py
import os, subprocess, copy, sys

class Package:
	def __init__(self):
		self.properties = {}
		self.build_steps = []

	def __init__(self, package_file):
		self.properties = {}
		self.build_steps = []

		self.loadPackage(package_file)


	#This function loads a package with build steps from a file
	def loadPackage(self, package_file):
		step_file = open(package_file, "r")
	
		build_step = []
		build_step.append({}) #0 index is a dictionary of config for the current build step
		build_step.append([]) #1 index is a list of build commands
	
		line = step_file.readline()
		while not line == "":
			if not (line[0] == "#" or line == ""):
				split_line = line.split("@=") #To allow equals signs in commands, use different here
				
				#Package properties
				if split_line[0] == "NAME":
					self.properties["NAME"] = split_line[1].split()[0] #Remove newline if applicable

				if split_line[0] == "REQUIREMENTS":
					self.properties["REQUIREMENTS"] = split_line[1].split()

				if split_line[0] == "PROVIDES":
					self.properties["PROVIDES"] = split_line[1].split()

				#Build step properties
				if split_line[0] == "ONLY_COMMANDS":
					build_step[0]["ONLY_COMMANDS"] = split_line[1]

				if split_line[0] == "ARCHIVE_NAME":
					build_step[0]["ARCHIVE_NAME"] = split_line[1]
				
				#Add the new path to the list, creating it if it doesn't exist
				if split_line[0] == "DOWNLOAD_PATH":
					inbetween = build_step[0].get("DOWNLOAD_PATH", [])
					inbetween.append(split_line[1])
					build_step[0]["DOWNLOAD_PATH"] = inbetween
	
				if split_line[0] == "BUILD_STEP":
					build_step[0]["BUILD_STEP"] = split_line[1]
	
				if split_line[0] == "CONFIGURE_COMMAND":
					build_step[1].append(split_line[1])
	
				if split_line[0] == "MAKE_COMMAND":
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
					while (line.split() == []) or not line.split()[0] == "END_COMMAND_BLOCK":	#Split to find first word
						build_step[1].append(line)
						line = step_file.readline()
	
				if (not line.split() == []) and (line.split()[0] == "END_BUILD_STEP"):
					self.build_steps.append(copy.deepcopy(build_step))
					build_step = [{},[]]
	
			line = step_file.readline()

		step_file.close()
	

	def build(self, begin_step, end_step, build_config, installed_packages, packages):
		script_string = ""
		#Go through our dependencies and build them
		if not (self.properties.get("REQUIREMENTS","None") == "None"):
			for requirement in self.properties["REQUIREMENTS"]:								#Get the individual requirements
				if installed_packages.get(requirement, "Not installed") == "Not installed":											#Check to see if we've already installed it
					script_string += packages[requirement].build(1, 0, build_config, installed_packages, packages)	#if not, get the package from the dictionary and build it

		begin_step -= 1 #0 indexed
		if end_step == 0:				#make 0 equal to the full lenght
			end_step = len(self.build_steps)

		#Setup a variable in the script for this program, for special stuff like the chroot thing we have to do for LFS builds
		script_string += "LBS_END_STEP=" + str(end_step) + "\n"
		for build_step_index in range(begin_step, end_step):
			script_string += "#################\n#################\n#################\n"
			script_string += self.buildStep(build_step_index, build_config)

		for provided in self.properties["PROVIDES"]:
			installed_packages[provided] = "True"

		return(script_string)

	def buildStep(self, build_step_index, build_config):
		script_string = ""
		build_step = self.build_steps[build_step_index]
		build_dir = build_config["BUILD_DIR"].split("\n")[0]
	
		#Change to the sources directory. All steps take place from here
		script_string += "cd " + build_dir + os.sep + "sources" + "\n"

		#Add download commands, if they exist
		if "DOWNLOAD_PATH" in build_step[0]:
			script_string += "#####DOWNLOADS#####\n"
			for download_path in build_step[0]["DOWNLOAD_PATH"]:
				download_path = download_path.split()[0]				#No trailing line returns or spaces
				download_name = download_path.split("/")[-1]			#Get the name by getting everything after the last "/"
				script_string += "##" + download_name + "##\n"
				script_string += "echo 'Testing for " + download_name +"!'\n"
				script_string += "if [ -s "+ download_name + " ]; then\n"
				script_string += "    echo '" + download_name + " exists!'\n"
				script_string += "else\n"
				script_string += "    echo '" + download_name + " does not exist, downloading!'\n"
				script_string += "    wget " + download_path + "\n"
				script_string += "fi\n"

	
		#If this step is only commands, not a pkg build, just output the commands and return
		if build_step[0].get("ONLY_COMMANDS", "False").split("\n")[0] == "True":
			for step in build_step[1]:
				script_string += step
			return(script_string)
	
	
		archive_name = build_step[0]["ARCHIVE_NAME"].split("\n")[0]
		archive_end = archive_name.split(".")[-1]
		extracted_dir = ".".join(archive_name.split(".")[:-2]) #Split on ".", remove the last two which are the line endings, then join with "." again to preserve version numbering
	
	
		#Extract
		if archive_end == "gz":
			extract_command = "tar xzvf " + archive_name
		elif archive_end == "bz2":
			extract_command = "bzip2 -cd " + archive_name + " | tar xvf -"
		elif archive_end == "xz":
			extract_command = "tar -Jxf " + archive_name
	
		script_string += extract_command + "\n"
		
	
		#Change dir
		script_string += "cd " + extracted_dir + "\n"
	
		#Follow build instructions
		for step in build_step[1]:
			script_string += step
	
		#change back to sources directory
		script_string += "cd " + build_dir.split("\n")[0] + os.sep + "sources" + "\n"
	
		#delete the extracted source directory and any build directories
		script_string += "rm " + "-rf " + extracted_dir + "\n"
		if build_step[0].get("EXTERNAL_BUILD_DIRECTORY", "False") == "True":
			script_string += "rm " +  "-rf " + build_step[0]["EXTERNAL_BUILD_DIRECTORY_LOCATION"] + "\n"
	
		#return our script to the top
		return(script_string)

	def listSteps(self):
		for build_step_index in range(len(self.build_steps)):
			 print(str(build_step_index+1), ":", self.build_steps[build_step_index][0]["BUILD_STEP"])