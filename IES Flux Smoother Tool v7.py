import numpy as np
import matplotlib.pyplot as plt
import shutil
import csv
from luxpy import iolidfiles as iolid
from scipy.interpolate import CubicSpline
from tkinter import *
from tkinter import filedialog


INITIAL_THETA = 0
FINAL_THETA = 90
IES_LOWER_CHAR_LIMIT = 230
IES_UPPER_CHAR_LIMIT = 240

#700mA-centered-std.ies
#erco-71505-000-en-ies - narrow spot.ies

def main():
    #obtains the IES file to work with from user via pop up
    root = Tk()
    root.withdraw()
    filename = filedialog.askopenfilename(title="Select A File", filetypes=(("ies", "*.ies"), ("other", "*.*")))
    root.destroy()
    root.mainloop()

    theta_res = ""
    #repeats asking for an input for the theta resolution until a proper input is given
    while ((not theta_res.isdigit() and not isfloat(theta_res)) or FINAL_THETA % float(theta_res) != 0):
        print()
        theta_res = input("Please input the desired theta resolution. (ex '0.5' or '1'): ")
        if (not theta_res.isdigit() and not isfloat(theta_res)):        #ensure that input number is a number
            print("ERROR: input a float/int type.")
        elif (FINAL_THETA % float(theta_res) != 0):                     #ensures the input number can divide 90
            print("ERROR: input a number that can divide 90.")
    theta_res = float(theta_res)            #changes the res from string value to a float

    original = filename
    target = filename[0:filename.index('.ies')]
    target += "_INTERP_res_" + str(theta_res) + ".ies"
    shutil.copyfile(original, target)

    IES = iolid.read_lamp_data(target, verbosity=1)           #reads and obtains IES data
    np.set_printoptions(floatmode='maxprec', suppress=True)     #makes the outputs not in scientific notation
    thetas = IES['theta']
    phis = IES["phi"]
    candelas = IES['candela_values']
    candelas_edit = np.reshape(candelas, (phis.size, thetas.size))  #reshapes so rows represent each phi, columns each theta

    print("Tasks:")
    print("1. Create a new IES file to contain interpolated values.")
    print("2. Obtain the entire interpolated array as a CSV file.")
    print("3. Obtain a single interpolated point as a CSV file.")

    task = ""
    # repeats asking for a task until a proper input is given
    while (task != "1" and task != "2" and task != "3"):
        print()
        task = input("Input the number of the task you would like to perform: ")
        if (task == "1"):
            edit_IES(phis, thetas, candelas_edit, target, theta_res)  #edits an IES file w
            print()
            print("IES file editted!")
        elif (task == "2"):
            np.set_printoptions(floatmode='fixed', suppress=True)       #changes number format to all have 8 digits -- easier to read
            arrays = multiple_phis_all_arrays(phis, thetas, candelas_edit, theta_res)

            with open("entire_interpolated_array_" + str(theta_res) + ".csv", "w") as array_file:   #creates CSV file w data
                maker = csv.writer(array_file)
                for item in arrays.items():
                    maker.writerow(item)
        elif (task == "3"):
            point = ""
            # repeats asking for a point until a proper input is given
            while ((not point.isdigit() and not isfloat(point)) or (FINAL_THETA % float(point) != 0) or (float(point) > 90 or float(point) < 0)):
                print()
                point = input("Provide the theta value for which you would like the interpolated intensity: ")
                if (not point.isdigit() and not isfloat(point)):        #ensures input is a number
                    print("ERROR: input a float/int type.")
                elif (float(point) > FINAL_THETA or float(point) < INITIAL_THETA):  #ensures point falls between the theta ranges
                    print("ERROR: point is not between 0-90.")
                elif (float(point) % theta_res != 0):       #ensures point can be obtained within the given theta resolution
                    print("ERROR: point is not present within current theta resolution.")
            point = float(point)
            np.set_printoptions(floatmode='fixed', suppress=True)   #changes number format to all have 8 digits -- easier to read
            print()
            final_point = single_point(thetas, candelas_edit, theta_res, point, phis)

            with open("single_points_" + str(theta_res) + ".csv", "w") as point_file:   #creates CSV file with data
                maker = csv.writer(point_file)
                for item in final_point.items():
                    maker.writerow(item)
        else:
            print("That task does not exist. Try again.")


# def browseFiles():
#     """Function for opening the file explorer window"""
#     filename = filedialog.askopenfilename(initialdir="/", title="Select a File",
#                                           filetypes=(("IES files", "*.ies*"), ("all files", "*.*")))

def isfloat(num):
    """function to check if an input is a float or not. Used to determine if inputs for point and theta_res are valid"""
    try:
        float(num)
        return True
    except ValueError:
        return False


def single_point(thetas, candelas_edit, theta_res, theta_val, phis):
    """returns all candela values associated with the given theta value for every phi present in the file."""
    phis_to_points = {}
    for i in range(phis.size):
        interp_array = interpolated_array(thetas, candelas_edit[i], theta_res)      #set var to interpolated array for inputted res
        for point in interp_array:              #looping thru interpolated array until the theta value is found
            if point[0] == theta_val:           #and returns the cadela value associated with it
                phis_to_points[phis[i]] = point
    return phis_to_points


def multiple_phis_all_arrays(phis, thetas, candelas_edit, theta_res):
    phi_to_interp = {}
    for i in range(phis.size):
        interp_array = interpolated_array(thetas, candelas_edit[i], theta_res)
        phi_to_interp[phis[i]] = interp_array
    return phi_to_interp


def interpolated_array(thetas, candelas, theta_res, for_replacing_candelas=False, for_replacing_thetas=False):
    """creates and returns the cubic spline interpolated array for a given theta resolution. Used when one phi/C"""
    cs = CubicSpline(thetas, candelas)  #creates cubic spline interpolated object function using theta and candela vals
    xnew = np.arange(thetas[0], thetas[-1] + theta_res, theta_res) #creates a new array from int-fin by inc of res
    splined = plt.plot(xnew, cs(xnew))  #plots so that x-axis= xnew & y-axis= interpolated object's function under xnew
    if (for_replacing_candelas):
        return splined[0].get_ydata()
    if (for_replacing_thetas):
        return splined[0].get_xdata()
    return splined[0].get_xydata()      #returning the splined plots points


def edit_IES(phis, thetas, candelas_edit, filename, theta_res):
    with open(filename, 'r') as file:
        data = file.read()                          #https://www.geeksforgeeks.org/how-to-search-and-replace-text-in-a-file-in-python/
        for i in range(phis.size):
            search_text_candelas = formatting_candelas(candelas_edit[i])
            replace_text_candelas = formatting_candelas(interpolated_array(thetas, candelas_edit[i], theta_res, True))       #NOTE: Choose own theta resolution!
            data = data.replace(search_text_candelas, replace_text_candelas)
        search_text_thetas = formatting_thetas(thetas)
        replace_text_thetas = formatting_thetas(interpolated_array(thetas, candelas_edit[0], theta_res, False, True))
        data = data.replace(search_text_thetas, replace_text_thetas)
        with open(filename, 'w') as write_file:
            write_file.write(data)

def formatting_candelas(curr_candelas):
    array_as_string = np.array2string(curr_candelas)
    format1 = " ".join(array_as_string.split())
    format2 = format1.replace("[", "").replace("]", "").replace(". ", ".0 ").replace(" 0.0 ", " 0 ")
    full = ""
    for i in range(1, int(np.ceil((len(format2) / IES_LOWER_CHAR_LIMIT))) + 1):
        if (len(format2) > 0):
            if (len(format2) < IES_LOWER_CHAR_LIMIT):       #When on the last line
                format2 = format2.replace(" 0. ", " 0 ").replace(" 0.0 ", " 0 ")    #more formatting
                if (format2[-1] == " "):            #for some reason some final finals end with a " " while others dont
                    full += format2[0:-1] + "\n"
                else:
                    full += format2 + "\n"
                format2 = ""            #setting format2 to nothing so that we don't repeat a line
            else:
                index = format2[IES_LOWER_CHAR_LIMIT: IES_UPPER_CHAR_LIMIT].find(" ") + IES_LOWER_CHAR_LIMIT
                first_part = format2[0: index]
                format2 = format2[index:]
                full += first_part + "\n"
    return full

def formatting_thetas(thetas):
    array_as_string = np.array2string(thetas)
    format1 = " ".join(array_as_string.split())
    format2 = format1.replace("[ ", "").replace("0. ]", "0").replace(". ", " ").replace("0.]", "0")
    full = ""
    for i in range(1, int(np.ceil((len(format2) / IES_LOWER_CHAR_LIMIT))) + 1):
        if (len(format2) > 0):
            if (len(format2) < IES_LOWER_CHAR_LIMIT ):  # When on the last line
                full += format2 + "\n"
                format2 = ""
            else:
                index = format2[IES_LOWER_CHAR_LIMIT: IES_UPPER_CHAR_LIMIT].find(" ") + IES_LOWER_CHAR_LIMIT
                first_part = format2[0: index]
                format2 = format2[index:]
                full += first_part + "\n"
    return full

if __name__ == "__main__":
    main()