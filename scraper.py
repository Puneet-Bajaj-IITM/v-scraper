from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from time import sleep
import pandas as pd
import re
import pandas as pd
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from time import sleep
import pandas as pd
import re
from datetime import datetime, timedelta
import schedule
import os
from time import sleep
from selenium.webdriver.chrome.options import Options
import schedule
import os
from time import sleep

def job(file_path):
    print(f"Running job with file path: {file_path}")
    main_with_retry(file_path)

def scrape(interval_days, file_path):
    if not os.path.exists('output'):
        os.makedirs('output')

    # Set the start time
    start_time = datetime.now()

    # Run the job for the first time
    job(file_path=file_path)

    # Schedule the job for subsequent runs
    schedule.every(interval_days).days.at(start_time.strftime("%H:%M")).do(job, file_path=file_path)

    # Run the scheduled jobs
    while True:
        try:
            schedule.run_pending()
            sleep(1)
        except Exception as e:
            # Catch any unexpected exceptions and print the error
            print(f"Error during scheduled job: {e}")

def main_with_retry(file_path):
    max_attempts = 3  # Maximum number of retry attempts
    attempt = 0

    while attempt <= max_attempts:
        try:
            main(file_path)
            break  # If successful, break out of the loop
        except (WebDriverException, NoSuchElementException) as e:
            print(f"Exception: {e}")
            print(f"Retrying after 10 seconds. Attempt {attempt}/{max_attempts}")
            sleep(10)  # Wait for 10 seconds before retrying
            attempt += 1
        except Exception as e:
            print(f"Unexpected Exception in main_with_retry: {e}")
            break  # Break out of the loop on unexpected exceptions

    if attempt > max_attempts:
        print("Max retry attempts reached. Exiting.")

def read_excel_to_df(file_path):
    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Error reading Excel file in read_excel_to_df: {e}")
        # Handle any exceptions, such as file not found or incorrect format
        return f"Error: {str(e)}"

def get_product_urls(df, column_name='product_name'):
    df[column_name] = df[column_name].replace(' ', '+', regex=True)
    df['url'] = df.apply(lambda row: f"https://www.amazon.in/s?k={row[column_name]}", axis=1)
    return df['url']

# Set up driver with user-agent rotation
ua = UserAgent()
user_agent = ua.random
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument(f"user-agent={user_agent}")
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def selenium_scrape(url):
    try:
        print(f"Processing URL: {url}")
        driver.get(url)
        sleep(1.5)  # Adjust wait time if needed

        products = []

        i = 0
        max_attempts = 3  # Maximum number of retry attempts

        while i < 2:
            try:
                            # Find the desired DIVs using the provided CSS selector
                filtered_divs = driver.find_elements(By.CSS_SELECTOR, 'div.sg-col-20-of-24.s-result-item.sg-col-0-of-12.sg-col-16-of-20.s-widget.sg-col.s-flex-geom.s-widget-spacing-small.sg-col-12-of-16')

                # Process the extracted data
                for div in filtered_divs:
                    prod_dict = {}

                    url_list = []
                    try:
                        for child in div.find_elements(By.CSS_SELECTOR, 'a.a-link-normal.s-no-outline'):
                            url = child.get_attribute('href')
                            url_list.append(url)
                        prod_dict['url'] = url_list[0] or "URL not found"

                        relevant_part = url.split("/dp/")[1]  # Split at "/dp/" and take the second part
                        match = re.search(r"^([^/]+)", relevant_part)  # Match non-slash characters at the beginning
                        if match:
                            product_id = match.group(1)  # Extract the matched group
                            prod_dict['ASIN'] = product_id or "ASIN ID not found"
                        else:
                            prod_dict['ASIN'] = "ASIN ID not found in the URL"

                    except:
                        prod_dict['url'] = "URL not found"
                        prod_dict['ASIN'] = "ASIN ID not found"
                    try:
                        image_list = []
                        for child in div.find_elements(By.CSS_SELECTOR, 'img.s-image'):
                            image_url = child.get_attribute('src')
                            image_text = child.get_attribute('alt')
                            image_srcset = child.get_attribute('srcset')
                            image_list.append(image_url)
                            image_list.append(image_text)
                            image_list.append(image_srcset)
                        prod_dict['image_url'] = image_list[0] or "Image URL not found"
                        prod_dict['image_text'] = image_list[1] or "Image Text not found"
                        prod_dict['image_srcset'] = image_list[2] or "Image Srcset not found"
                    except:
                        prod_dict['image_url'] = "Image URL not found"
                        prod_dict['image_text'] = "Image Text not found"
                        prod_dict['image_srcset'] = "Image Srcset not found"

                    try:
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-size-base.s-underline-text'):
                            num_reviews = child.text
                            prod_dict['num_reviews'] = num_reviews or "Number of Reviews not found"
                    except:
                        prod_dict['num_reviews'] = "Number of Reviews not found"

                    try:
                        item_sold = []
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-size-base.a-color-secondary'):
                            sold = child.text
                            item_sold.append(sold)
                        prod_dict['item_sold'] = item_sold[0] or "Items Sold not found"
                    except:
                        prod_dict['item_sold'] = "Items Sold not found"

                    try:
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-price-whole'):
                            price = child.text
                            prod_dict['price'] = price or "Price not found"
                    except:
                        prod_dict['price'] = "Price not found"

                    try:
                        ppn_list = []
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-size-base.a-color-secondary'):
                            ppn_list.append(child.text or "Price per unit not found")
                        prod_dict['ppn'] = ppn_list[1].replace('\n', '').replace('(', '').replace(')', '') or "Price per unit not found"
                    except:
                        prod_dict['ppn'] = "Price per unit not found"

                    try:
                        mrp_list = []
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-price.a-text-price'):
                            mrp_list.append(child.text)
                        prod_dict['mrp'] = mrp_list or "MRP not found"
                    except:
                        prod_dict['mrp'] = "MRP not found"

                    try:
                        for child in div.find_elements(By.CSS_SELECTOR, 'span.a-color-base.a-text-bold'):
                            delivery = child.text
                            prod_dict['delivery'] = delivery or "Delivery not found"
                    except:
                        prod_dict['delivery'] = "Delivery not found"

                    products.append(prod_dict)

                i += 1
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, 'a.s-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator')  # Find parent anchor tag
                    if next_button:
                        next_button.click()
                        driver.implicitly_wait(2)
                    else:
                        driver.implicitly_wait(2)
                except Exception as e:
                    print(f"Error finding or clicking next button: {e}")
                    print(f"Retrying after 2 seconds...")
                    sleep(2)  # Wait for 2 seconds before retrying
                    continue  # Continue the loop to retry finding and clicking the next button
                except:
                    raise Exception("No next button found")
            except (WebDriverException, NoSuchElementException) as e:
                print(f"Exception: {e}")
                print(f"Retrying after 10 seconds. Attempt {i}/{max_attempts}")
                sleep(10)  # Wait for 10 seconds before retrying
                continue  # Continue the loop to retry on exception
            return products
    except Exception as e:
        # Log the error and continue (or retry) depending on your requirements
        print(f"Unexpected Exception in selenium_scrape: {e}")


import datetime

def main(file_path):
    try:
        df = read_excel_to_df(file_path)

        if df is not None:
            urls_series = get_product_urls(df, column_name='keywords')
            data_series = urls_series.apply(selenium_scrape)
            # Close the browser
            driver.quit()

        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file_name = f'output_file_{current_time}.xlsx'

        # Create a Pandas Excel writer using ExcelWriter
        with pd.ExcelWriter(f'output/{output_file_name}', engine='xlsxwriter') as writer:
            for i, (row, data) in enumerate(zip(df.iterrows(), data_series)):
                index, row_data = row
                attempt = 0
                max_attempts = 3  # Maximum number of retry attempts
                while attempt <= max_attempts:
                    try:
                        # Create a DataFrame from the list of dictionaries
                        subsheet_df = pd.DataFrame(data)
                        subsheet_df['mrp'] = subsheet_df['mrp'].apply(lambda x: max(map(int, re.findall(r'\d+', str(x)))) if x else None)  # Convert 'mrp' to integer
                        # Use the value from the 'keywords' column of the corresponding row in df as the subsheet name
                        subsheet_name = str(row_data['keywords']) if i < len(df) else f'SubSheet_{i + 1}'
                        subsheet_df.to_excel(writer, index=False, sheet_name=subsheet_name)
                        break  # Break out of the retry loop if successful
                    except Exception as e:
                        # Log the error and retry
                        print(f"Error processing row {i} - Attempt {attempt + 1}/{max_attempts}: {e}")
                        attempt += 1
                        if attempt <= max_attempts:
                            print(f"Retrying after 10 seconds...")
                            sleep(10)  # Wait for 10 seconds before retrying
                        else:
                            print(f"Max retry attempts reached for row {i}. Skipping.")
                            break  # Break out of the retry loop if max attempts reached

        # Save the Excel file
        print(f"Excel file {output_file_name} has been created.")
    
    except Exception as e:
        # Handle any unexpected exceptions at the top level
        print(f"Unexpected Exception in main: {e}")
       

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
from time import sleep
import pandas as pd
import re
from datetime import datetime, timedelta
import schedule
from time import sleep

# scrape(file_path='data.xlsx', interval_days=1)
