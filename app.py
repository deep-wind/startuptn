# -*- coding: utf-8 -*-
"""
Created on Sun Jul 25 00:23:57 2021

@author: PRAMILA
"""

import datetime
import json
import numpy as np
import requests
import base64
import pandas as pd
import streamlit as st
from copy import deepcopy
from fake_useragent import UserAgent
#from footer_utils import image, link, layout, footer
# = UserAgent()
#browser_header = {'User-Agent': temp_user_agent.random}

# browser_header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
# browser_header = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; ONEPLUS A6000) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36'}

st.set_page_config(layout='wide',
                   initial_sidebar_state='collapsed',
                   page_icon="https://www.cowin.gov.in/favicon.ico",
                   page_title="CoWIN Vaccination Slot Availability")


def get_base64_of_bin_file(bin_file):
    """
    function to read png file 
    ----------
    bin_file: png -> the background image in local folder
    """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    """
    function to display png as bg
    ----------
    png_file: png -> the background image in local folder
    """
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    body {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    
    st.markdown(page_bg_img, unsafe_allow_html=True)
    return



set_png_as_page_bg('vac1.gif')
     

@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def load_mapping():
    df = pd.read_csv("district_mapping.csv")
    return df

def filter_column(df, col, value):
    df_temp = deepcopy(df.loc[df[col] == value, :])
    return df_temp

def filter_capacity(df, col, value):
    df_temp = deepcopy(df.loc[df[col] > value, :])
    return df_temp

@st.cache(allow_output_mutation=True)
def Pageviews():
    return []

mapping_df = load_mapping()

rename_mapping = {
    'date': 'Date',
    'min_age_limit': 'Minimum Age Limit',
    'available_capacity': 'Available Capacity',
    'vaccine': 'Vaccine',
    'pincode': 'Pincode',
    'name': 'Hospital Name',
    'state_name' : 'State',
    'district_name' : 'District',
    'block_name': 'Block Name',
    'fee_type' : 'Fees'
    }
nav = st.sidebar.radio("Choose your Language",["Home 🏡","English","Tamil"])
if nav == "English":
    set_png_as_page_bg('vac7.jpg')
    st.title('COVID19 Vaccine Slot Management System')
    with st.beta_expander("ONLINE BOOKING"):
        valid_states = list(np.unique(mapping_df["state_name"].values))
        
        left_column_1, center_column_1, right_column_1 = st.beta_columns(3)
        with left_column_1:
            numdays = st.number_input('No. of days',min_value=0,max_value=100,value=1,step=1)      
        
        with center_column_1:
            state_inp = st.selectbox('Select State', [""] + valid_states)
            if state_inp != "":
                mapping_df = filter_column(mapping_df, "state_name", state_inp)
        
        
        mapping_dict = pd.Series(mapping_df["district id"].values,
                                 index = mapping_df["district name"].values).to_dict()
        
        # numdays = st.sidebar.slider('Select Date Range', 0, 100, 10)
        unique_districts = list(mapping_df["district name"].unique())
        unique_districts.sort()
        with right_column_1:
            dist_inp = st.selectbox('Select District', unique_districts)
        
        DIST_ID = mapping_dict[dist_inp]
        
        base = datetime.datetime.today()
        date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
        date_str = [x.strftime("%d-%m-%Y") for x in date_list]
        
        temp_user_agent = UserAgent()
        browser_header = {'User-Agent': temp_user_agent.random}
        
        final_df = None
        for INP_DATE in date_str:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_ID, INP_DATE)
            response = requests.get(URL, headers=browser_header)
            if (response.ok) and ('centers' in json.loads(response.text)):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode("sessions")
                        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                        df['date'] = df.sessions.apply(lambda x: x['date'])
                        df = df[["date", "available_capacity", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                else:
                    st.error("No rows in the data Extracted from the API")
        #     else:
        #         st.error("Invalid response")
        
        if (final_df is not None) and (len(final_df)):
            final_df.drop_duplicates(inplace=True)
            final_df.rename(columns=rename_mapping, inplace=True)
        
            left_column_2, center_column_2, right_column_2, right_column_2a,  right_column_2b = st.beta_columns(5)
            with left_column_2:
                valid_pincodes = list(np.unique(final_df["Pincode"].values))
                pincode_inp = st.selectbox('Select Pincode', [""] + valid_pincodes)
                if pincode_inp != "":
                    final_df = filter_column(final_df, "Pincode", pincode_inp)
        
            with center_column_2:
                valid_age = [18, 45]
                age_inp = st.selectbox('Select Minimum Age', [""] + valid_age)
                if age_inp != "":
                    final_df = filter_column(final_df, "Minimum Age Limit", age_inp)
        
            with right_column_2:
                valid_payments = ["Free", "Paid"]
                pay_inp = st.selectbox('Select Free or Paid', [""] + valid_payments)
                if pay_inp != "":
                    final_df = filter_column(final_df, "Fees", pay_inp)
        
            with right_column_2a:
                valid_capacity = ["Available"]
                cap_inp = st.selectbox('Select Availablilty', [""] + valid_capacity)
                if cap_inp != "":
                    final_df = filter_capacity(final_df, "Available Capacity", 0)
        
            with right_column_2b:
                valid_vaccines = ["COVISHIELD", "COVAXIN"]
                vaccine_inp = st.selectbox('Select Vaccine', [""] + valid_vaccines)
                if vaccine_inp != "":
                    final_df = filter_column(final_df, "Vaccine", vaccine_inp)
        
            table = deepcopy(final_df)
            table.reset_index(inplace=True, drop=True)
            st.table(table)
        
    df1=pd.read_excel('tnhospitals.xlsx')
    
    
    with st.beta_expander("TELEPHONE BOOKING"):
       # data=pd.DataFrame(columns=['State'])
       # st.table(df)
        col1,col2 = st.beta_columns(2) 
        with col1:
            valid_states = list(np.unique(df1["State"].values))
            valid_states1 = st.selectbox('Select state', [""] + valid_states)
        # valid_dis = list(np.unique(df["District"].values))
        # valid_dis1 = st.selectbox('Select district', [""] + valid_dis)
        with col2:
            unique_districts = list(df1["District"].unique())
            unique_districts.sort()
            unique_districts=st.selectbox('Select district', [""] + unique_districts)
        valid_hospital= list(np.unique(df1["Hospital_Name"].values))
        valid_hospital1 = st.selectbox('Select hospital', [""] + valid_hospital)
        if(st.button("search")):
           rslt_df = df1[(df1['Hospital_Name']==valid_hospital1) & (df1['District']==unique_districts)]
           rslt_df.reset_index(inplace=True, drop=True)
           st.table(rslt_df)
           
if nav == "Tamil":     
    set_png_as_page_bg('vac7.jpg')
    st.title('COVID19 Vaccine Slot Management System')
    with st.beta_expander("ஆன்லைன் முன்பதிவு"):
        valid_states = list(np.unique(mapping_df["state_name"].values))
        
        left_column_1, center_column_1, right_column_1 = st.beta_columns(3)
        with left_column_1:
            numdays = st.number_input('நாட்களின் எண்ணிக்கை',min_value=0,max_value=100,value=1,step=1)
        
        with center_column_1:
            state_inp = st.selectbox('மாநிலத்தைத் தேர்ந்தெடுக்கவும்', [""] + valid_states)
            if state_inp != "":
                mapping_df = filter_column(mapping_df, "state_name", state_inp)
        
        
        mapping_dict = pd.Series(mapping_df["district id"].values,
                                 index = mapping_df["district name"].values).to_dict()
        
        # numdays = st.sidebar.slider('Select Date Range', 0, 100, 10)
        unique_districts = list(mapping_df["district name"].unique())
        unique_districts.sort()
        with right_column_1:
            dist_inp = st.selectbox('மாவட்டத்தைத் தேர்ந்தெடுக்கவும்', unique_districts)
        
        DIST_ID = mapping_dict[dist_inp]
        
        base = datetime.datetime.today()
        date_list = [base + datetime.timedelta(days=x) for x in range(numdays)]
        date_str = [x.strftime("%d-%m-%Y") for x in date_list]
        
        temp_user_agent = UserAgent()
        browser_header = {'User-Agent': temp_user_agent.random}
        
        final_df = None
        for INP_DATE in date_str:
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(DIST_ID, INP_DATE)
            response = requests.get(URL, headers=browser_header)
            if (response.ok) and ('centers' in json.loads(response.text)):
                resp_json = json.loads(response.text)['centers']
                if resp_json is not None:
                    df = pd.DataFrame(resp_json)
                    if len(df):
                        df = df.explode("sessions")
                        df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
                        df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
                        df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity'])
                        df['date'] = df.sessions.apply(lambda x: x['date'])
                        df = df[["date", "available_capacity", "vaccine", "min_age_limit", "pincode", "name", "state_name", "district_name", "block_name", "fee_type"]]
                        if final_df is not None:
                            final_df = pd.concat([final_df, df])
                        else:
                            final_df = deepcopy(df)
                else:
                    st.error("தரவில் வரிசைகள் எதுவும் API இருந்து பிரித்தெடுக்கப்படவில்லை")
        #     else:
        #         st.error("Invalid response")
        
        if (final_df is not None) and (len(final_df)):
            final_df.drop_duplicates(inplace=True)
            final_df.rename(columns=rename_mapping, inplace=True)
        
            left_column_2, center_column_2, right_column_2, right_column_2a,  right_column_2b = st.beta_columns(5)
            with left_column_2:
                valid_pincodes = list(np.unique(final_df["Pincode"].values))
                pincode_inp = st.selectbox('பின்கோடு', [""] + valid_pincodes)
                if pincode_inp != "":
                    final_df = filter_column(final_df, "Pincode", pincode_inp)
        
            with center_column_2:
                valid_age = [18, 45]
                age_inp = st.selectbox('குறைந்தபட்ச வயதைத் தேர்ந்தெடுக்கவும்', [""] + valid_age)
                if age_inp != "":
                    final_df = filter_column(final_df, "Minimum Age Limit", age_inp)
        
            with right_column_2:
                valid_payments = ["Free", "Paid"]
                pay_inp = st.selectbox('இலவச அல்லது கட்டணத்தைத் தேர்ந்தெடுக்கவும் ', [""] + valid_payments)
                if pay_inp != "":
                    final_df = filter_column(final_df, "Fees", pay_inp)
        
            with right_column_2a:
                valid_capacity = ["Available"]
                cap_inp = st.selectbox('கிடைக்கும் என்பதைத் தேர்ந்தெடுக்கவும்', [""] + valid_capacity)
                if cap_inp != "":
                    final_df = filter_capacity(final_df, "Available Capacity", 0)
        
            with right_column_2b:
                valid_vaccines = ["COVISHIELD", "COVAXIN"]
                vaccine_inp = st.selectbox('தடுப்பூசி தேர்ந்தெடுக்கவும்: *கோவிஷீல்ட் ;*கோவாக்சின்', [""] + valid_vaccines)
                if vaccine_inp != "":
                    final_df = filter_column(final_df, "Vaccine", vaccine_inp)
        
            table = deepcopy(final_df)
            table.reset_index(inplace=True, drop=True)
            st.table(table)
    df1=pd.read_excel('tnhospitals.xlsx')
    
    
    with st.beta_expander("டெலிஃபோன் புக்கிங்"):
       # data=pd.DataFrame(columns=['State'])
       # st.table(df)
        col1,col2 = st.beta_columns(2) 
        with col1:
             valid_states = list(np.unique(df1["State"].values))
             valid_states1 = st.selectbox('மாநிலத்தைத் தேர்ந்தெடுக்கவும்', [""] + valid_states)
        
        with col2:
             unique_districts = list(df1["District"].unique())
             unique_districts.sort()
             unique_districts=st.selectbox('மாவட்டத்தைத் தேர்ந்தெடுக்கவும்', [""] + unique_districts)
        valid_hospital= list(np.unique(df1["Hospital_Name"].values))
        valid_hospital1 = st.selectbox('மருத்துவமனையைத் தேர்ந்தெடுக்கவும்', [""] + valid_hospital)
        if(st.button("தேடு")):
           rslt_df = df1[(df1['Hospital_Name']==valid_hospital1) & (df1['District']==unique_districts)]
           rslt_df.reset_index(inplace=True, drop=True)
           st.table(rslt_df)
