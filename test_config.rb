#!/usr/bin/env ruby

require 'yaml'
require 'awesome_print'

ap YAML.load_file('configuration.yaml')
