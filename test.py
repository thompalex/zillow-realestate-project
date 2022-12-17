# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# import time


# options = Options() 
# options.add_argument("download.default_directory=./data/test/")

# prefs = {"download.default_directory" : "C:\\Users\\alex_\\CS\\class\\econ312\\zillow-realestate-project\\data\\test"}

# options.add_experimental_option("prefs", prefs)
# options.add_argument('--headless')

# dr = webdriver.Chrome(options=options)

# dr.get('https://www.zillow.com/research/data/')

# def select_string(x): 
#     return f'ZHVI {x}-Bedroom Time Series ($)'

# for i in range(1, 6):
#     s = 'ZHVI 5+ Bedroom Time Series ($)'
#     if i < 5:
#         s = select_string(i)
#     dr.find_element(By.XPATH, f'//option[contains(text(),"{s}")]').click()
#     dr.find_element(By.XPATH, '//option[text()="Neighborhood"]').click()
#     dr.find_element(By.XPATH, '//a[@id="median-home-value-zillow-home-value-index-zhvi-download-link"]').click()
#     time.sleep(5)

# time.sleep(30)
    
 
import hashlib
import requests

def check_for_plagiarism(code):
    # Hash the code using the SHA-256 algorithm
    hashed_code = hashlib.sha256(code.encode()).hexdigest()

    # Use the requests library to search the target website for code with the same hash
    website_url = "https://www.hackerrank.com/search?query=" + hashed_code
    response = requests.get(website_url)
    print(response.text)

    # If the website returns a 200 status code (success), the code is likely copied
    if response.status_code == 200:
        return "Code is likely copied from the website"
    # If the website returns a 404 status code (not found), the code is likely original
    elif response.status_code == 404:
        return "Code is likely original"
    # If the website returns any other status code, there was an error
    else:
        return "An error occurred while checking for plagiarism"


print(check_for_plagiarism('''function dayOfProgrammer(year) {
    // Write your code here
  if(year==1918){
    return "26.09."+year;
  }
  
  else if(year<1918){
    if(year%4==0){
      return "12.09."+year;
    }
    else{
      return "13.09."+year; 
    }
  }
  else if(year>1918){
    if((year%400==0) || ((year%4==0) && !(year%100==0))) {
      return "12.09."+year;
    }
    else{
      return "13.09."+year;
    }
    
  }
}'''))

