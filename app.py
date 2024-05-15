import streamlit as st
import requests
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from time import sleep
from urllib.parse import quote
import argparse
import base64

from function import get_paperinfo, get_tags, get_papertitle, get_citecount, get_link, get_author_year_publi_info, cite_number, convert_df
from springer_function import scrape_and_store_links

st.set_page_config(page_title="Paper Information Scraper", layout="wide")
html_temp = """
                    <div style="background-color:{};padding:1px">
                    
                    </div>
                    """

with st.sidebar:
    st.markdown("""
    # About
    A tool to extract relevant information of research papers from Google Scholar, Springer and Nature based on user input. 
    """)
    
    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)
    st.markdown("""
    # How does it work?
    Enter your keywords in the text field to scrape the result.  
    """)

hide="""
<style>
footer{
	visibility: hidden;
    	position: relative;
}
.viewerBadge_container__1QSob{
    visibility: hidden;
}

<style>
"""
st.markdown(hide, unsafe_allow_html=True)

# title
st.markdown("""
## Paper Information Scraper
Scraping relevant information of research papers.
""")
tab1, tab2, tab3= st.tabs(["Google Scholar", "Springer", "Nature"])

with tab1:
    # scraping function
    # creating final repository
    paper_repos_dict = {
                        'Paper Title' : [],
                        'Year' : [],
                        'Author' : [],
                        'Citation' : [],
                        'Publication site' : [],
                        'Url of paper' : [] }

    # adding information in repository
    def add_in_paper_repo(papername,year,author,cite,publi,link):
        paper_repos_dict['Paper Title'].extend(papername)
        paper_repos_dict['Year'].extend(year)
        paper_repos_dict['Author'].extend(author)
        paper_repos_dict['Citation'].extend(cite)
        paper_repos_dict['Publication site'].extend(publi)
        paper_repos_dict['Url of paper'].extend(link)
        #   for i in paper_repos_dict.keys():
        #     print(i,": ", len(paper_repos_dict[i]))
        #     print(paper_repos_dict[i])
        df = pd.DataFrame(paper_repos_dict)
        
        return df

    # headers
    headers = {'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    url_begin = 'https://scholar.google.com/scholar?start={}&q='
    url_end = '&hl=en&as_sdt=0,5='

    text_input = st.text_input("Search in Google Scholar", placeholder="What are you looking for?", disabled=False)

    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)
    # create scholar url
    if text_input:
        text_formated = "+".join(text_input.split())
        input_url = url_begin+text_formated+url_end
        if input_url:
            response=requests.get(input_url,headers=headers)
            for i in range (1,6):
                # get url for the each page
                url = input_url.format(i)
                # function for the get content of each page
                doc = get_paperinfo(url, headers)

                # function for the collecting tags
                paper_tag,cite_tag,link_tag,author_tag = get_tags(doc)

                # paper title from each page
                papername = get_papertitle(paper_tag)

                # year , author , publication of the paper
                year , publication , author = get_author_year_publi_info(author_tag)

                # cite count of the paper 
                cite = get_citecount(cite_tag)

                # url of the paper
                link = get_link(link_tag)

                # add in paper repo dict
                final = add_in_paper_repo(papername,year,author,cite,publication,link)

                # use sleep to avoid status code 429
                sleep(20)
            
            final['Year'] = final['Year'].astype('int')
            final['Citation'] = final['Citation'].apply(cite_number).astype('int')

            with st.expander("Extracted papers"):
                st.dataframe(final)
                csv = convert_df(final)
                file_name_value = "_".join(text_input.split())+'.csv'
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name=file_name_value,
                    mime='text/csv',
                )

with tab2:
    def get_topic_springer(topic):
        topic_repos_url = 'https://link.springer.com/search?query=' + topic
        response = requests.get(topic_repos_url)
        if response.status_code != 200:
            st.error(f"Failed to fetch web page: {topic_repos_url}")
            raise Exception(f"Failed to fetch web page: {topic_repos_url}")

        doc = BeautifulSoup(response.text, 'html.parser')
        return doc

    # Streamlit UI
    query = st.text_input("Search in Springer", placeholder= "What are you looking for?", disabled=False)

    url_query = quote(query)
    topic_url = f"https://link.springer.com/search?query={url_query}"

    doc = get_topic_springer(url_query)
    
    start_url = topic_url
    target_count = 50

    result_df = scrape_and_store_links(start_url, target_count)
    custom_css = """
<style>
    /* Adjust the width of the DataFrame table */
    .dataframe {
        width: 100%; /* Adjust the width of the DataFrame */
    }
</style>
"""
    st.write(custom_css, unsafe_allow_html=True)

    st.markdown(html_temp.format("rgba(55, 53, 47, 0.16)"),unsafe_allow_html=True)


    with st.expander("Extracted papers"):
        st.dataframe(result_df)
        csv = convert_df(result_df)
        file_name_value = "_".join(query.split())+'.csv'
        download_button_key1 = "my_unique_download_button"

        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=file_name_value,
            mime='text/csv',key= download_button_key1)

    def get_abstract(url):
        r = requests.get(url) 
        soup = BeautifulSoup(r.content, 'html.parser')
        abstract = soup.find('div', attrs={'id': 'Abs1-content'})
        if abstract:
            return abstract.p.text.replace('\n','')
        else:
            ul_element = soup.find('ul', class_='c-book-show-more-less', id='unique-selling-points')
            li_texts = []
            for li in ul_element.find_all('li'):
                li_texts.append(li.text.strip())
            return '\n'.join(li_texts)

    def process_csv(file):
        if file is None:
            print("No file uploaded")

            #st.error("No file uploaded.")
            return None

        df = pd.read_csv(file)
        fieldnames = ['Title', 'URL', 'abstract']
        errors = []
        row_count = 1
        for index, row in df.iterrows():
            try:
                abstract = get_abstract(row['URL'])
                df.loc[index, 'abstract'] = abstract
            except AttributeError as e:
                df.loc[index, 'abstract'] = "ABSTRACT NOT FOUND ERROR"
                print("Error at row ", row_count, ":", e)
                errors.append(row_count)
                print("Processed row #", row_count)
            row_count += 1
        return df

    st.subheader("Upload downloaded file for absract scraping")

    # Create a file uploader widget
    file_uploader = st.file_uploader("Select a CSV file", type=["csv"])

        # Process the uploaded file
    df = process_csv(file_uploader)
    if df is not None:
            # Convert the DataFrame to a CSV string
        csv_data = df.to_csv(index=False)

            # Create a download button
        st.download_button("Download processed CSV file", csv_data, "output.csv", "text/csv")
    else:
        print("No file uploaded")
        #st.error("No file uploaded or processing failed.")

        # Create a download button
    #csv_data = df.to_csv(index=False)
    #st.download_button("Download processed CSV file", csv_data, "output.csv", "text/csv")

with tab3:
        # Streamlit UI
    query = st.text_input("Search in Nature", placeholder= "What are you looking for?", disabled=False)

    url_query = quote(query)
    topic_url = f"https://link.springer.com/search?query={url_query}"

    doc = get_topic_springer(url_query)
    def get_topic_nature(topic):
        topic_repos_url = 'https://www.nature.com/search?q='+ topic
        response = requests.get(topic_repos_url)
        print(topic_repos_url)
        doc = BeautifulSoup(response.text)
        return doc
    
    doc = get_topic_nature(url_query)
    link_elements = doc.find_all('h3', class_='c-card__title')

    data = []

# Iterate over each h3 element in link_elements
    for link_element in link_elements:
        # Find the <a> element within the h3 element
        a_element = link_element.find('a', class_='c-card__link')
        
        # If <a> element is found, extract URL and title
        if a_element:
            base_url = "https://www.nature.com"
            relative_url = a_element['href']
            url = urllib.parse.urljoin(base_url, relative_url)
            title = a_element.text.strip()
            
            # Append URL and title to data list
            data.append({'URL': url, 'Title': title})
        else:
        # Append a placeholder value or perform other action
            data.append({'URL': 'N/A', 'Title': 'No Title'})


    # Create a dataframe from the data list
    nature_df = pd.DataFrame(data)

    with st.expander("Extracted papers"):
            st.dataframe(nature_df)
            csv = convert_df(nature_df)
            file_name_value = "_".join(query.split())+'.csv'
            download_button_key__2 = "my_download_button"

            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=file_name_value,
                mime='text/csv', key = download_button_key__2)
    
    def get_abstract(url):
        r = requests.get(url) 
        soup = BeautifulSoup(r.content, 'html.parser')
        abstract = soup.find('div', attrs={'id': 'Abs1-content'})
        if abstract:
            return abstract.p.text.replace('\n','')
        else:
            # If the <div> element is not found, return None or any other default value indicating that the abstract is not available
            return None

    def process_csv(file):
        if file is None:
            print("No file uploaded")

            #st.error("No file uploaded.")
            return None

        df1 = pd.read_csv(file)
        fieldnames = ['Title', 'URL', 'abstract']
        errors = []
        row_count = 1
        for index, row in df1.iterrows():
            try:
                abstract = get_abstract(row['URL'])
                df1.loc[index, 'abstract'] = abstract
            except AttributeError as e:
                df1.loc[index, 'abstract'] = "ABSTRACT NOT FOUND ERROR"
                print("Error at row ", row_count, ":", e)
                errors.append(row_count)
                print("Processed row #", row_count)
            row_count += 1
        return df1

    st.subheader("Upload downloaded file for absract scraping")

    # Create a file uploader widget
    file_uploader = st.file_uploader("Select a CSV file", type=["csv"],key='file_uploader')

        # Process the uploaded file
    df1 = process_csv(file_uploader)
    if df1 is not None:
            # Convert the DataFrame to a CSV string
        csv_data = df1.to_csv(index=False)

            # Create a download button
        st.download_button("Download processed CSV file", csv_data, "output.csv", "text/csv")
    else:
        print("No file uploaded")
        #st.error("No file uploaded or processing failed.")
