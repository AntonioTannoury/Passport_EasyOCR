import cv2
import time
import easyocr
import numpy as np
import streamlit as st
from OCR_utils import (
    MRZ_lines,
    prep_MRZ1,
    prep_MRZ2,
    validity_checks,
    refine_output,
    crop_mrz,
)

print("Loading Reader...")
reader = easyocr.Reader(["en"])
print("Reader Loaded")

##### Application #####
PAGE_CONFIG = {"page_title": "StColab.io", "page_icon": ":smiley:", "layout": "wide"}
st.set_page_config(**PAGE_CONFIG)


def main():
    st.sidebar.title("ID verification APP")
    menu = ["Passport OCR", "Face Recognition and Liveness Check"]
    choice = st.sidebar.selectbox("Menu", menu)
    Debug = st.sidebar.checkbox("Debug")

    if choice == "Passport OCR":
        rectKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
        sqKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))

        st.header("""Please Upload a clear scanned photo of your passport""")

        uploaded_file = st.file_uploader("Upload Files", type=["png", "jpeg", "jpg"])
        if uploaded_file is not None:
            file_details = {
                "FileName": uploaded_file.name,
                "FileType": uploaded_file.type,
                "FileSize": uploaded_file.size,
            }

            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            opencv_image = cv2.imdecode(file_bytes, 1)
            time0 = time.time()

            img = opencv_image.copy()
            w = int(img.shape[1] * 0.5)
            result = reader.readtext(img, min_size=w)
            extraction_time = time.time() - time0

            mrz = MRZ_lines(result)
            mrz1 = prep_MRZ1(mrz["mrz1"])
            mrz2 = prep_MRZ2(mrz["mrz2"])
            validity = validity_checks(mrz2, with_Overall=False)

            ocr_df = refine_output(mrz1, mrz2, validity)
            roi_mrz1 = crop_mrz(mrz["mrz1_borders"], img)
            roi_mrz2 = crop_mrz(mrz["mrz2_borders"], img)

            st.write("Time:{} sec".format(round(extraction_time, 2)))

            # Now dsiplay the image and OCR:
            col1, col2 = st.columns(2)
            # column 1
            col1.header("Passport Image")
            col1.image(opencv_image, channels="BGR")

            # column 2
            col2.header("Passport OCR")

            if float(ocr_df[ocr_df["Data Field"] == "Validation Score"].Value) >= 60:
                col2.dataframe(ocr_df, width=2000, height=600)
            else:
                col2.dataframe(ocr_df, width=2000, height=600)
                col2.write(
                    "Invalide OCR Extraction or Fraudulent Document . Please Rescan..."
                )
                # col2.dataframe(df)
            if Debug:
                st.header("ROI")

                st.write("MRZ1:" + mrz["mrz1"])
                st.write(mrz1)
                st.image(roi_mrz1, channels="BGR")

                st.write("MRZ2:" + mrz["mrz2"])
                st.write(mrz2)
                st.image(roi_mrz2, channels="BGR")

    elif choice == "Face Recognition and Liveness Check":
        st.subheader("App Under Development \U0001f600")


if __name__ == "__main__":
    main()
# %%
