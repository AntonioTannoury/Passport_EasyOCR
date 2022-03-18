import re
import cv2
import pycountry
import pandas as pd
from datetime import datetime, date


# Functions
def delete_multiple_element(list_object, indices):
    listt = list_object.copy()
    indices = sorted(indices, reverse=True)
    for idx in indices:
        if idx < len(listt):
            listt.pop(idx)
    return listt


def MRZ_lines(result):
    pops = []
    for i, r in enumerate(result):
        if "<" in r[1]:
            pass
        else:
            pops.append(i)
    results = delete_multiple_element(result, pops)

    if result[0][0][0][1] < result[1][0][0][1]:
        mrz1 = result[0][1]
        mrz2 = result[1][1]
    else:
        mrz1 = result[1][1]
        mrz2 = result[0][1]
    MRZ = {'mrz1':mrz1,
          'mrz1_borders': results[0][0],
          'mrz2':mrz2,
          'mrz2_borders': results[1][0]}    
    return MRZ


def prep_MRZ1(mrz1):
    mrz1 = mrz1.upper()
    mrz1 = mrz1.replace("0", "O")
    mrz1 = mrz1.replace(" ", "")
    mrz1 = re.sub("[!@#$_-]", "", mrz1)
    mrz1 = re.sub("\d+", "<", mrz1)

    if mrz1[0] == "P":
        doc_type = "Passport"
    else:
        doc_type = "Other"

    issue_country = mrz1[2:5].replace("8", "B").replace("0", "O")
    print(issue_country)
    issue_country = pycountry.countries.get(alpha_3=issue_country).name

    endLN = mrz1.index("<<")
    LN = mrz1[5:endLN].replace("<", " ")

    beginFN = mrz1.index("<<") + 2
    endFN = mrz1.index("<<", mrz1.index("<<") + 2)
    FN = mrz1[beginFN:endFN].replace("<", " ")

    mrz1_info = {
        "doc_type": doc_type,
        "issue_country": issue_country,
        "LN": LN,
        "FN": FN,
    }
    return mrz1_info


def prep_MRZ2(mrz2):
    mrz2 = mrz2.upper()
    mrz2 = mrz2.replace(" ", "")
    mrz2 = re.sub("[!@#$_-]", "", mrz2)
    todays_date = date.today()

    PN = mrz2[0:9].replace("O", "0").replace("<", "")
    PN_cd = mrz2[9]

    Nationality = mrz2[10:13].replace("8", "B").replace("0", "O")
    Nationality = pycountry.countries.get(alpha_3=Nationality).name

    DOB = mrz2[13:19]
    DOB = str(datetime.strptime(DOB, "%y%m%d"))[:-9]
    if int(DOB[0:4]) > todays_date.year:
        DOB = "19" + DOB[2:]
    DOB_cd = mrz2[19]

    Gender = mrz2[20]
    if Gender == "F":
        Gender = "Female"
    elif Gender == "M":
        Gender = "Male"

    Pass_Exp = mrz2[21:27]
    Pass_Exp = str(datetime.strptime(Pass_Exp, "%y%m%d"))[:-9]
    Pass_Exp_cd = mrz2[27]

    mrz2_c = mrz2[0:9] + mrz2[9:].replace("<", "")

    PersN = mrz2_c[28:-2]
    PersN_cd = mrz2_c[-2]

    Overall_cd = mrz2_c[-1]

    mrz2_info = {
        "PN": PN,
        "PN_cd": PN_cd,
        "Nationality": Nationality,
        "DOB": DOB,
        "DOB_cd": DOB_cd,
        "Gender": Gender,
        "Pass_Exp": Pass_Exp,
        "Pass_Exp_cd": Pass_Exp_cd,
        "PersN": PersN,
        "PersN_cd": PersN_cd,
        "Overall_cd": Overall_cd,
        "MRZ2": mrz2,
    }
    return mrz2_info


def CHECK_DIGIT(txt):
    CHECK_CODES = dict()
    for i in range(10):
        CHECK_CODES[str(i)] = i
    for i in range(ord("A"), ord("Z") + 1):
        CHECK_CODES[chr(i)] = i - 55  # A --> 10, B --> 11, etc
    CHECK_CODES["<"] = 0
    CHECK_WEIGHTS = [7, 3, 1]

    if txt == "":
        return str(0)
    res = sum(
        [CHECK_CODES.get(c, -1000) * CHECK_WEIGHTS[i % 3] for i, c in enumerate(txt)]
    )
    if res < 0:
        return ""
    else:
        return str(res % 10)


def validity_checks(
    mrz2,
    with_Overall=True,
    avg=True,
    w_PN=0,
    w_DOB=0,
    w_Pass_Exp=0,
    w_PersN=0,
    w_Overal=0,
):
    # Personal Number Check
    PN = mrz2["PN"]
    PN_cd = mrz2["PN_cd"]
    calc_PN_cd = CHECK_DIGIT(PN)
    check_PN = calc_PN_cd == PN_cd

    # Date of Birth Check
    DOB = mrz2["MRZ2"][13:19]
    DOB_cd = mrz2["DOB_cd"]
    calc_DOB_cd = CHECK_DIGIT(DOB)
    check_DOB = calc_DOB_cd == DOB_cd

    # Passport Expiery Check
    Pass_Exp = mrz2["MRZ2"][21:27]
    Pass_Exp_cd = mrz2["Pass_Exp_cd"]
    calc_Pass_Exp_cd = CHECK_DIGIT(Pass_Exp)
    check_Pass_Exp = calc_Pass_Exp_cd == Pass_Exp_cd

    # Personal Number Check
    PersN = mrz2["PersN"]
    PersN_cd = mrz2["PersN_cd"]
    calc_PersN_cd = CHECK_DIGIT(PersN)
    check_PersN = calc_PersN_cd == PersN_cd

    # Overal
    Overal = mrz2["MRZ2"][:-1]
    Overal_cd = mrz2["Overall_cd"]
    calc_Overal_cd = CHECK_DIGIT(PersN)
    check_Overal = calc_Overal_cd == Overal_cd

    # Score
    if avg:
        if with_Overall:
            score = round(
                100
                * (check_PN + check_DOB + check_Pass_Exp + check_PersN + check_Overal)
                / 5,
                2,
            )
        else:
            score = round(
                100 * (check_PN + check_DOB + check_Pass_Exp + check_PersN) / 4, 2
            )
    else:
        if with_Overall:
            w_sum = w_PN + w_DOB + w_Pass_Exp + w_PersN + w_Overal
            score = round(
                100
                * (
                    w_PN * check_PN
                    + w_DOB * check_DOB
                    + w_Pass_Exp * check_Pass_Exp
                    + w_PersN * check_PersN
                    + w_Overal * check_Overal
                )
                / w_sum,
                2,
            )
        else:
            w_sum = w_PN + w_DOB + w_Pass_Exp + w_PersN
            score = round(
                100
                * (
                    w_PN * check_PN
                    + w_DOB * check_DOB
                    + w_Pass_Exp * check_Pass_Exp
                    + w_PersN * check_PersN
                )
                / w_sum,
                2,
            )

    checks = {
        "check_PN": check_PN,
        "calc_PN_cd": calc_PN_cd,
        "check_DOB": check_DOB,
        "calc_DOB_cd": calc_DOB_cd,
        "check_Pass_Exp": check_Pass_Exp,
        "calc_Pass_Exp_cd": calc_Pass_Exp_cd,
        "check_PersN": check_PersN,
        "calc_PersN_cd": calc_PersN_cd,
        "check_Overal": check_Overal,
        "calc_Overal_cd": calc_Overal_cd,
        "score": score,
    }
    return checks


def refine_output(mrz1, mrz2, validity):

    json_data = {
        "Issuing Counrty": mrz1["issue_country"],
        "First Name": mrz1["FN"],
        "Last Name": mrz1["LN"],
        "Passport Number": mrz2["PN"],
        "Nationality": mrz2["Nationality"],
        "Date of Birth": mrz2["DOB"],
        "Gender": mrz2["Gender"],
        "Passport Expiry": mrz2["Pass_Exp"],
        "Personal Number": mrz2["PersN"],
        "Validation Score": validity["score"],
    }
    check_digits_list = [
        "-",
        "-",
        "-",
        mrz2["PN_cd"],
        "-",
        mrz2["DOB_cd"],
        "-",
        mrz2["Pass_Exp_cd"],
        mrz2["PersN_cd"],
        "-",
    ]
    calc_check_digits_list = [
        "-",
        "-",
        "-",
        validity["calc_PN_cd"],
        "-",
        validity["calc_DOB_cd"],
        "-",
        validity["calc_Pass_Exp_cd"],
        validity["calc_PersN_cd"],
        "-",
    ]

    flags = [
        "-",
        "-",
        "-",
        validity["check_PN"],
        "-",
        validity["check_DOB"],
        "-",
        validity["check_Pass_Exp"],
        validity["check_PersN"],
        "-",
    ]
    for i in range(len(flags)):
        if flags[i] == True:
            flags[i] = "✅"
        elif flags[i] == False:
            flags[i] = "❌"

    output_df = pd.DataFrame(
        list(
            zip(
                list(json_data.keys()),
                list(json_data.values()),
                check_digits_list,
                calc_check_digits_list,
                flags,
            )
        ),
        columns=[
            "Data Field",
            "Value",
            "Ext. Check Digit",
            "Calc. Check Digit",
            "Validation",
        ],
    ).astype(str)
    return output_df


def crop_mrz(borders_list, image):
    x1, y1 = borders_list[0]
    x2, y2 = borders_list[1]
    x3, y3 = borders_list[2]
    x4, y4 = borders_list[3]

    top_left_x = min([x1, x2, x3, x4])
    top_left_y = min([y1, y2, y3, y4])
    bot_right_x = max([x1, x2, x3, x4])
    bot_right_y = max([y1, y2, y3, y4])

    cropped = image[top_left_y : bot_right_y + 1, top_left_x : bot_right_x + 1]
    return cropped
