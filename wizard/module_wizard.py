#!/usr/bin/env python

#module_wizard v.2.0
#08.11.2019

glob_fileName = 'jsonData.js'
glob_jsonDict = {}

def communicate():
	print("the file \"" + glob_fileName + "\" has been created.")

def dump_jsFile():
	global glob_fileName
	js_input = "let jsonData = " + json.dumps(glob_jsonDict)

	os.chdir("wizard")
	with open(glob_fileName, "w+") as js_data:
		js_data.write(js_input)

def create_moduleDict(module, module_settings):
	# 'module_settings = None' if no required or optionals settings were found
	module_dict = {}

	if module_settings == None:
		module_dict = {	
				"name":module, 
				"installed":True
			}
	else:
		module_dict = {	
				"name":module, 
				"installed":True,
				"settings": module_settings
			}

	return(module_dict)

def rearrange_settings(key, yaml_input):
	settings = yaml_input[key]
	settings_list = []

	for setting in settings:
		temp_dir = {}
		temp_dir["name"] = setting
		for entry in settings[setting]:
			temp_dir[entry] = settings[setting][entry]
		
		settings_list.append(temp_dir)

	return (settings_list)

def extract_settings(yaml_input):
	settings = {}
	setting_check = False

	for key in yaml_input:
		if key == "required_settings":
			setting_check = True
			settings["required"] = rearrange_settings(key, yaml_input)
		if key == "optional_settings":
			setting_check = True
			settings["optional"] = rearrange_settings(key, yaml_input)
		if key == "columns":
			setting_check = True
			settings["columns"] = rearrange_settings(key, yaml_input)

	if setting_check == False:
		settings = None

	return (settings)

def file_loop(root, folder, module):
	global glob_jsonDict
	options_yaml = None
	options_path = root + "/" + folder + "/" + module

	for f in os.listdir(options_path):
		if f.endswith(".yml") or f.endswith(".yaml"):
			with open(options_path + "/" + f) as yamlf:
				options_yaml = yaml.load(yamlf, Loader=yaml.SafeLoader)

	return(options_yaml)

def module_loop(root, folder):
	global glob_jsonDict
	glob_jsonDict[folder]["modules"] = []
	module_list = glob_jsonDict[folder]["modules"]

	for module in os.listdir(root + "/" + folder):
		module_name = module
		if module_name != "none":
			module_yaml = file_loop(root, folder, module)
			module_settings = extract_settings(module_yaml)
			module_dict = create_moduleDict(module, module_settings)

			module_list.append(module_dict)
		else:
			## module dict for none:
			## in html page storage
			pass

def folder_loop():
	global glob_jsonDict

	os.chdir("..")
	root_folder = "dge_pipeline/snakefiles"
	for folder in os.listdir(root_folder):
		glob_jsonDict[folder] = {"groupName":folder}
		module_loop(root_folder, folder)

def main():
	folder_loop()
	dump_jsFile()
	communicate()

if __name__ == "__main__":
	import json
	import yaml
	import os
	import re
	main()