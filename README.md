## 🏥 Doctor Fee Prediction - Bangalore Practo Scraper

This project creates a web interface that allows users to predict doctor consultation fees based on input data. The machine learning model is trained on a dataset obtained by scraping data from the Practo website using a **robots.txt compliant** Scrapy + Playwright implementation.

### 🚀 **New Scraping Implementation**

The scraper has been completely redesigned to:
- ✅ **Respect robots.txt** - No longer uses disallowed search URLs
- ✅ **Navigate naturally** - Starts from https://www.practo.com/bangalore and follows site structure
- ✅ **JavaScript support** - Uses Playwright for heavy JavaScript navigation
- ✅ **Focused approach** - Specifically targets Bangalore doctors as requested

### 🔧 **How It Works**

```
1. Start at https://www.practo.com/bangalore
2. Discover specialty pages (e.g., /bangalore/cardiologist-doctors)  
3. Navigate through each specialty to find doctors
4. Extract individual doctor profile data
```

### 🏃‍♂️ **Quick Start**

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the scraper
python run_bangalore_scraper.py
```

### 📋 **Usage Examples**

```bash
# Basic usage
python run_bangalore_scraper.py

# Custom output file
python run_bangalore_scraper.py --output bangalore_doctors.csv

# Run with visible browser (for debugging)
python run_bangalore_scraper.py --headless=false

# Limit results for testing
python run_bangalore_scraper.py --limit 50

# Verbose logging
python run_bangalore_scraper.py --verbose
```

### 🤖 **Robots.txt Compliance**

The scraper respects Practo's robots.txt by:
- ❌ Avoiding search URLs (`/*?searchfor=doctor&q=*`)
- ❌ Not using general search endpoints (`/search*`)
- ✅ Using natural site navigation
- ✅ Following profile URLs which are allowed
### 📊 **Data Output**

The scraper extracts:
- 👨‍⚕️ **Doctor Name**
- 🏥 **Specialty** (Cardiologist, Dentist, etc.)
- 📅 **Years of Experience**
- 📍 **Location/Area**
- ⭐ **Rating/Score**
- 💰 **Consultation Fee**
- 🔗 **Profile URL**

### 🗂️ **Project Structure**

```
Doctor-Fee-Prediction-Model/
├── requirements.txt                    # Dependencies
├── config.py                          # Configuration settings
├── run_bangalore_scraper.py           # Main runner script
├── practo_scraper/                    # Scrapy project
│   ├── scrapy.cfg                    # Scrapy configuration
│   └── practo_scraper/
│       ├── settings.py               # Scrapy settings
│       ├── items.py                  # Data structure definitions
│       ├── pipelines.py              # Data processing pipelines
│       ├── middlewares.py            # Custom middlewares
│       └── spiders/
│           ├── bangalore_doctors.py  # Main robots.txt compliant spider
│           └── __init__.py
└── data/                             # Output directory
    └── *.csv                        # Generated data files
```

### ⚙️ **Configuration**

Edit `config.py` to customize:
- **Base URLs** and target pages
- **CSS Selectors** for data extraction  
- **Browser settings** for Playwright
- **Output format** and file naming

### 🛡️ **Ethical Scraping**

This implementation follows best practices:
- ✅ Respects robots.txt completely
- ✅ Conservative request delays (3+ seconds)
- ✅ Single concurrent request per domain
- ✅ Proper user agent identification
- ✅ Graceful error handling

   
## Findings from the Doctor Fee Prediction Project 🧪

- According to the Practo dataset, Bangalore has the highest number of doctors.

<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(493).png" width="700" >

 
- The most common degrees among doctors are MBBS, MD, and BDS, with the highest representation in the dataset.
  
<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(492).png" width="800" >

  
- The dataset indicates that the three most prominent specialties among doctors are:
  - Dentist
  - Gynecologist
  - Pediatrician

<img src="https://github.com/Vishwanath-J-25/Doctor-Fee-Prediction-Model/blob/main/githu/Screenshot%20(494).png" width="800" >


        
 <br>


## 🏥 Doctor Fee Prediction ML Model Creation Steps 🧠

<img src="https://github.com/Sannidhi-Shetty2/Doctor-Fee-Prediction/assets/62684303/b5ff0161-b645-4677-80f8-5520e5ecf3d9" width="800" >

**1. Data Collection:** Gathered doctor-related information from Practo using web scraping techniques with Selenium.

**2. Data Preprocessing:** Conducted thorough data cleaning, handling missing values, and transforming categorical variables into numerical representations.

**3. Feature Engineering:** Derived additional relevant features from the existing dataset, such as extracting qualifications.

**4. Model Selection:** Explored various regression algorithms and selected potential candidates based on initial performance evaluation.

**5. Hyperparameter Tuning:** Utilized GridSearchCV to fine-tune hyperparameters for each selected model, optimizing their performance.

**6. Model Training:** Trained multiple models on the dataset with the tuned hyperparameters to improve predictive accuracy.

**7. Weighted Voting:** Implemented a Weighted Voting technique, combining predictions from multiple models, each with a specific weight.

**8. Model Evaluation:** Evaluated the ensemble model using appropriate metrics such as Mean Absolute Error (MAE) or Root Mean Squared Error (RMSE) to measure prediction accuracy.

**9. Web App Development:** Developed a user-friendly web application using Flask, HTML, and CSS to offer an intuitive interface for users to input parameters.

## 🏥 Doctor Fee Prediction Web application

 <p align="center"><img src="https://github.com/Sannidhi-Shetty2/Doctor-Fee-Prediction/assets/62684303/92d53380-68d4-4289-8d43-4e386d3b2025" width="500" ></p>

## 🏥 Challenges and Learnings

**1. Data Extraction:** We intially faced difficulties to get the data from the server,as
we had to explore it, and tried to figure it out.. 

**2. Model Selection:**  Explored different ML models to identify the Best models.

**3. Hyperparameter Tunning:**  Hyperparameter tuning was time-consuming due to limited time for model development

**4. Creating the webpage:**  As we are new to this concept, this was quiet challenging and
interesting in creating it.

 
## 🏥 Conclusion

**1. Healthcare Accessibility:** By giving patients an idea of potential costs, it helps them seek appropriate medical care without the barrier of uncertainty about fees.

**2. Transparency and Trust:**  Clear fee estimates foster trust and confidence in medical services, enhancing the doctor-patient relationship.

**3. Efficiency for Providers:** With fee estimates readily available, administrative processes become smoother, leading to improved overall service efficiency.
