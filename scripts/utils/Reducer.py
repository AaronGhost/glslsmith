# Copyright 2021 The glslsmith Project Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from xml.dom import minidom


class Reducer:
    def __init__(self, reducer_name, reducer_command, interesting_test, reducer_input_name, reducer_output_name,
                 extra_files):
        self.name = reducer_name
        self.command = reducer_command
        self.interesting_test = interesting_test
        self.input_file = reducer_input_name
        self.output_files = reducer_output_name
        self.extra_files_to_build = extra_files

    def __str__(self):
        return self.name

    @staticmethod
    def load_reducers_settings(filename):
        xmldoc = minidom.parse(filename)
        reducers = []
        reducerxml = xmldoc.getElementsByTagName("reducer")
        for reducer in reducerxml:
            name = reducer.getElementsByTagName("name")[0].childNodes[0].data
            reducer_command = reducer.getElementsByTagName("command")[0].childNodes[0].data
            interesting_test = reducer.getElementsByTagName("interesting")[0].childNodes[0].data
            input_name = reducer.getElementsByTagName("input_file")[0].childNodes[0].data
            output_name = reducer.getElementsByTagName("output_file")[0].childNodes[0].data
            extra_files = []
            extra_file_xml = reducer.getElementsByTagName("extra_files")
            if extra_file_xml.length != 1:
                nb_files = int(extra_file_xml.getElementByTagName("length")[0].childNodes[0].data)
                for i in range(nb_files):
                    extra_files.append(extra_file_xml.getElementByTagName("file_" + str(i)[0]).childNodes[0].data)
            reducers.append(Reducer(name, reducer_command, interesting_test, input_name, output_name, extra_files))
        return reducers
