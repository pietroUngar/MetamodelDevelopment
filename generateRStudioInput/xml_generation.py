import xml.etree.ElementTree as ETree
import matplotlib.pyplot as plt
from tkinter import filedialog
from sklearn.svm import SVC
import numpy, xlrd, os
import tkinter as tk


def calculate_metamodel_error(input_dict: dict, output_dict: dict, metamodel, check_func=None, first_row=1,
                              first_col=0):
    root = tk.Tk()
    root.withdraw()
    excel_path = filedialog.askopenfilename()
    file = xlrd.open_workbook(excel_path)

    return_dict = __return_values(

        sheets=file.sheets(), n_input=len(input_dict["names"]), n_output=len(output_dict["names"]),
        check_func=check_func, first_row=first_row, first_col=first_col

    )

    input_dict.update({"values": return_dict["input"]})
    output_dict.update({"values": return_dict["output"]})

    create_rstudio_xml(os.path.dirname(excel_path), input_dict, output_dict)

    return {"input": input_dict, "output": output_dict}


def convert_excel_to_xml(input_dict: dict, output_dict: dict, check_func=None, first_row=1, first_col=0):
    root = tk.Tk()
    root.withdraw()
    excel_path = filedialog.askopenfilename()
    file = xlrd.open_workbook(excel_path)

    return_dict = __return_values(

        sheets=file.sheets(), n_input=len(input_dict["names"]), n_output=len(output_dict["names"]),
        check_func=check_func, first_row=first_row, first_col=first_col

    )

    input_dict.update({"values": return_dict["input"]})
    output_dict.update({"values": return_dict["output"]})

    create_rstudio_xml(__get_destination_dir(), input_dict, output_dict)

    return {"input": input_dict, "output": output_dict}


def __get_destination_dir():

    xml_destination_file = os.path.join(os.path.dirname(__file__), "xml_destination.dat")

    xml_destination = ""

    if os.path.isfile(xml_destination_file):

        with open(xml_destination_file, "r") as file:

            xml_destination = file.readline().strip("\n")

    if not os.path.exists(xml_destination):

        root = tk.Tk()
        root.withdraw()
        xml_destination = filedialog.askdirectory()

        with open(xml_destination_file, "w") as file:

            file.write(xml_destination)

    return xml_destination


def __return_values(sheets, n_input, n_output, check_func=None, first_row=1, first_col=0):
    input_values_list = __generate_value_list(n_input)
    output_values_list = __generate_value_list(n_output)

    if check_func is None:
        def check_func(input_list):
            return True

    for sheet in sheets:

        for row in range(first_row, len(sheet.col_values(first_col))):

            if type(sheet.cell_value(row, first_col)) is float:

                if check_func(sheet.row_values(row, start_colx=first_col)):

                    input_values_list = __append_values(input_values_list, sheet, row, first_col)
                    output_values_list = __append_values(output_values_list, sheet, row, first_col + n_input)

    return {"input": input_values_list, "output": output_values_list}


def __generate_value_list(n_value) -> list:
    new_list = list()

    for i in range(n_value):
        new_list.append(list())

    return new_list


def __append_values(input_list: list, sheet, row, offset) -> list:
    for col in range(offset, offset + len(input_list)):

        try:
            input_list[col - offset].append(float(sheet.cell_value(row, col)))

        except:
            input_list[col - offset].append(0)

    return input_list


def __calculate_error(input_dict, output_dict, metamodel):
    return {"input": input_dict, "output": output_dict}


def create_rstudio_xml(folder_path, input_dict, output_dict):
    data = generate_xml(input_dict, output_dict)
    file_path = os.path.join(folder_path, "data.xml")

    xml_file = open(file_path, "wb")
    xml_file.write(ETree.tostring(data))
    xml_file.close()


def generate_xml(input_dict, output_dict) -> ETree.Element:

    root = ETree.Element("data")
    root.set("n_exp", str(len(input_dict["values"][0])))

    inputs = ETree.SubElement(root, "inputs")
    inputs.set("n_input", str(len(input_dict["values"])))

    outputs = ETree.SubElement(root, "outputs")
    outputs.set("n_output", str(len(output_dict["values"])))

    for dict in [input_dict, output_dict]:

        if dict == input_dict:

            parent = inputs
            name = "input"

        else:

            parent = outputs
            name = "output"

        for i in range(len(dict["values"])):

            sub_element = ETree.SubElement(parent, name)

            sub_element.set("index", str(i + 1))

            sub_element.set("name", dict["names"][i])
            sub_element.set("measure_unit", dict["units"][i])

            sub_element.set("max", str(numpy.max(dict["values"][i])))
            sub_element.set("min", str(numpy.min(dict["values"][i])))
            sub_element.set("mean", str(numpy.nanmean(dict["values"][i])))

            value_str = str(dict["values"][i][0])
            for value in dict["values"][i][1:]:
                value_str += ";" + str(value)

            sub_element.set("values", value_str)

    return root


def generate_SVM(return_dict, x_index, y_index):
    input_values_list = return_dict["input"]["values"]
    output_values_list = return_dict["output"]["values"]

    input_names_list = return_dict["input"]["names"]
    input_units_list = return_dict["input"]["units"]

    fig1, ax = plt.subplots()

    x = numpy.array(input_values_list).transpose()

    model = SVC(kernel='linear', C=1E10)
    model.fit(x, output_values_list[-1])

    ax.scatter(input_values_list[x_index], input_values_list[y_index], c=output_values_list[-1])
    ax.set_xlabel(input_names_list[x_index] + " " + input_units_list[x_index])
    ax.set_ylabel(input_names_list[y_index] + " " + input_units_list[y_index])

    counter_dict = dict()

    for value in output_values_list[-1]:

        value = '{:0>4}'.format(int(value))

        if value in counter_dict.keys():

            counter_dict[value] += 1

        else:

            counter_dict[value] = 1

    print(counter_dict)

    plt.show()


if __name__ == "__main__":

    print(__get_destination_dir())
