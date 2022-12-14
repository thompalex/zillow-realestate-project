from selenium import webdriver
from selenium.webdriver.common.by import By


chrome_options = webdriver.ChromeOptions()
prefs = {'download.default_directory' : './data/test/'}
chrome_options.add_experimental_option('prefs', prefs)
dr = webdriver.Chrome(chrome_options=chrome_options)

dr.get('https://www.zillow.com/research/data/')

def select_string(x): 
    return f'ZHVI {x}-Bedroom Time Series ($)'

for i in range(1, 6):
    s = 'ZHVI 5+ Bedroom Time Series ($)'
    if i < 5:
        s = select_string(i)
    dr.find_element(By.XPATH, f'//option[contains(text(),"{s}")]').click()
    dr.find_element(By.XPATH, '//option[text()="Neighborhood"]').click()
    dr.find_element(By.XPATH, '//a[@id="median-home-value-zillow-home-value-index-zhvi-download-link"]').click()
    
 

