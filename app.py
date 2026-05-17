import os
import shutil
import zipfile
import pandas as pd
import requests
from PIL import Image
import streamlit as st
import urllib3

# -----------------------------------
# DISABLE SSL WARNINGS
# -----------------------------------
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# -----------------------------------
# STREAMLIT PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Company Logo Downloader",
    layout="wide"
)

st.title("Company Logo Downloader")

st.write(
    "Upload Excel file and download company logos"
)

# -----------------------------------
# BRAND FETCH CLIENT ID
# -----------------------------------
CLIENT_ID = "1idqr4ZwAUltaEPorND"

# -----------------------------------
# CREATE MAIN LOGOS FOLDER
# -----------------------------------
os.makedirs("logos", exist_ok=True)

# -----------------------------------
# FILE UPLOADER
# -----------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# -----------------------------------
# REMOVE WHITE BACKGROUND
# -----------------------------------
def remove_white_background(image_path):

    try:

        img = Image.open(image_path).convert("RGBA")

        datas = img.getdata()

        new_data = []

        for item in datas:

            # Detect white background
            if (
                item[0] > 240
                and item[1] > 240
                and item[2] > 240
            ):

                # Make transparent
                new_data.append((255, 255, 255, 0))

            else:

                new_data.append(item)

        img.putdata(new_data)

        img.save(image_path, "PNG")

    except:
        pass

# -----------------------------------
# DOWNLOAD LOGO
# -----------------------------------
def download_logo(company, domain):

    company_folder = f"logos/{company}"

    os.makedirs(company_folder, exist_ok=True)

    logo_urls = [

        # Best wide logo
        f"https://cdn.brandfetch.io/"
        f"{domain}/w/1200/h/300/logo?c={CLIENT_ID}",

        # Medium logo
        f"https://cdn.brandfetch.io/"
        f"{domain}/w/800/h/200/logo?c={CLIENT_ID}",

        # Default fallback
        f"https://cdn.brandfetch.io/"
        f"{domain}?c={CLIENT_ID}"
    ]

    headers = {

        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": (
            "image/avif,image/webp,"
            "image/apng,image/svg+xml,"
            "image/*,*/*;q=0.8"
        ),

        "Referer": "https://brandfetch.com/",

        "Origin": "https://brandfetch.com"
    }

    best_score = -1

    best_file = None

    # -----------------------------------
    # TRY DIFFERENT SOURCES
    # -----------------------------------
    for i, url in enumerate(logo_urls):

        try:

            response = requests.get(

                url,

                headers=headers,

                timeout=20,

                verify=False,

                allow_redirects=True
            )

            content_type = response.headers.get(
                "Content-Type",
                ""
            )

            # -----------------------------------
            # VALID IMAGE
            # -----------------------------------
            if (
                response.status_code == 200
                and "image" in content_type
            ):

                temp_path = (
                    f"{company_folder}/temp_{i}.png"
                )

                # Save temporary image
                with open(temp_path, "wb") as file:

                    file.write(response.content)

                try:

                    img = Image.open(temp_path)

                    width, height = img.size

                    ratio = width / height

                    score = 0

                    # Prefer wide logos
                    if ratio > 4:

                        score += 50

                    elif ratio > 2:

                        score += 30

                    elif ratio > 1:

                        score += 10

                    # Prefer higher resolution
                    if width > 1000:

                        score += 30

                    elif width > 500:

                        score += 20

                    # Remove white background
                    remove_white_background(
                        temp_path
                    )

                    # Keep best logo
                    if score > best_score:

                        best_score = score

                        best_file = temp_path

                except:

                    continue

        except:
            pass

    # -----------------------------------
    # SAVE BEST LOGO ONLY
    # -----------------------------------
    if best_file:

        final_path = (
            f"{company_folder}/best_logo.png"
        )

        # Delete old best logo
        if os.path.exists(final_path):

            os.remove(final_path)

        # Copy best temp file
        shutil.copy(
            best_file,
            final_path
        )

        # -----------------------------------
        # DELETE ALL TEMP FILES
        # -----------------------------------
        for file_name in os.listdir(company_folder):

            if file_name.startswith("temp_"):

                temp_path = os.path.join(
                    company_folder,
                    file_name
                )

                try:

                    os.remove(temp_path)

                except:
                    pass

        return final_path

    return None

# -----------------------------------
# PROCESS UPLOADED FILE
# -----------------------------------
if uploaded_file:

    try:

        # Read Excel
        df = pd.read_excel(uploaded_file)

        st.success(
            "Excel File Loaded Successfully"
        )

        # -----------------------------------
        # VALIDATE REQUIRED COLUMNS
        # -----------------------------------
        required_columns = [
            "company",
            "domain"
        ]

        for col in required_columns:

            if col not in df.columns:

                st.error(
                    f"Missing column: {col}"
                )

                st.stop()

        # -----------------------------------
        # PROCESS BUTTON
        # -----------------------------------
        process_button = st.button(
            "Download Logos"
        )

        # -----------------------------------
        # START PROCESSING
        # -----------------------------------
        if process_button:

            # Clean previous ZIP if exists
            if os.path.exists("logos.zip"):

                os.remove("logos.zip")

            progress_bar = st.progress(0)

            total_rows = len(df)

            # -----------------------------------
            # PROCESS EACH COMPANY
            # -----------------------------------
            for index, row in df.iterrows():

                # Skip empty rows
                if (
                    pd.isna(row["company"])
                    or pd.isna(row["domain"])
                ):
                    continue

                company = (
                    str(row["company"])
                    .strip()
                )

                domain = (
                    str(row["domain"])
                    .strip()
                )

                st.subheader(
                    f"Processing: {company}"
                )

                logo_path = download_logo(
                    company,
                    domain
                )

                # -----------------------------------
                # DISPLAY RESULT
                # -----------------------------------
                if logo_path:

                    st.success(
                        f"{company} logo downloaded"
                    )

                    st.image(
                        logo_path,
                        width=400
                    )

                else:

                    st.error(
                        f"Logo not found for {company}"
                    )

                # -----------------------------------
                # UPDATE PROGRESS BAR
                # -----------------------------------
                progress = (
                    (index + 1)
                    / total_rows
                )

                progress_bar.progress(progress)

            # -----------------------------------
            # CREATE ZIP FILE
            # -----------------------------------
            zip_path = "logos.zip"

            with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED
            ) as zipf:

                for root, dirs, files in os.walk("logos"):

                    for file in files:

                        file_path = os.path.join(
                            root,
                            file
                        )

                        zipf.write(
                            file_path,
                            os.path.relpath(
                                file_path,
                                "logos"
                            )
                        )

            # -----------------------------------
            # DOWNLOAD ZIP BUTTON
            # -----------------------------------
            with open(zip_path, "rb") as file:

                st.download_button(

                    label="Download All Logos ZIP",

                    data=file,

                    file_name="logos.zip",

                    mime="application/zip"
                )

            st.success(
                "All logos processed successfully"
            )

    except Exception as e:

        st.error(
            f"Error reading Excel file: {e}"
        )