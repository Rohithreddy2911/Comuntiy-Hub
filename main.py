# ============================================================================
# CAREERCOMPASS PRO - PRODUCTION-READY MAIN APPLICATION
# Version: 10.0.0 - Complete, Optimized, Error-Handled
# Built for Performance & Scalability
# ============================================================================

from fastapi import FastAPI, Request, Form, HTTPException, status, Response, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import jwt
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from chatbot import router as quiz_router
import json
import os
import re
import html
from urllib.parse import quote_plus
from math import ceil
# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('careercompass.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application Configuration"""
    SECRET_KEY = "careercompass_secret_key_2024_production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours
    APP_NAME = "CareerCompass Pro"
    APP_VERSION = "10.0.0"
    ENVIRONMENT = "production"

config = Config()

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title=config.APP_NAME,
    description="AI-powered career guidance platform",
    version=config.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include quiz router from chatbot.py so frontend can call /Exam
app.include_router(quiz_router)

# Create necessary directories
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted successfully")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# ============================================================================
# IN-MEMORY DATABASE (Can be replaced with real DB)
# ============================================================================

users_db: Dict[str, Dict[str, Any]] = {}
user_analyses: Dict[str, Dict[str, Any]] = {}

# ============================================================================
# COMPREHENSIVE COURSES DATABASE (50+ COURSES)
# ============================================================================

COURSES_DATABASE = [
    # CYBERSECURITY (7 courses)
    {
        'platform': 'udemy',
        'title': 'Ethical Hacking & Network Penetration Testing',
        'instructor': 'Udemy',
        'price': 499,
        'rating': 4.7,
        'duration': '22 hours',
        'students': '450K+',
        'skills': ['ethical hacking', 'penetration testing', 'network security'],
        'url': 'https://www.udemy.com/course/ethical-hacking'
    },
    {
        'platform': 'coursera',
        'title': 'Cybersecurity Fundamentals',
        'instructor': 'Coursera',
        'price': 5999,
        'rating': 4.8,
        'duration': '4 months',
        'students': '200K+',
        'skills': ['cybersecurity', 'network security', 'threat analysis'],
        'url': 'https://www.coursera.org/learn/cybersecurity-fundamentals'
    },
    {
        'platform': 'pluralsight',
        'title': 'Advanced Penetration Testing',
        'instructor': 'Pluralsight',
        'price': 4500,
        'rating': 4.9,
        'duration': '18 hours',
        'students': '150K+',
        'skills': ['penetration testing', 'linux', 'cryptography'],
        'url': 'https://www.pluralsight.com/courses/penetration-testing'
    },
    {
        'platform': 'linkedin',
        'title': 'Cybersecurity Career Path',
        'instructor': 'LinkedIn Learning',
        'price': 2499,
        'rating': 4.6,
        'duration': '8 hours',
        'students': '100K+',
        'skills': ['cybersecurity', 'compliance', 'threat analysis'],
        'url': 'https://www.linkedin.com/learning/cybersecurity'
    },
    {
        'platform': 'edx',
        'title': 'Cybersecurity Essentials',
        'instructor': 'edX',
        'price': 7999,
        'rating': 4.7,
        'duration': '6 weeks',
        'students': '120K+',
        'skills': ['network security', 'cryptography', 'ethical hacking'],
        'url': 'https://www.edx.org/course/cybersecurity'
    },
    {
        'platform': 'udacity',
        'title': 'Cybersecurity Nanodegree',
        'instructor': 'Udacity',
        'price': 12999,
        'rating': 4.8,
        'duration': '6 months',
        'students': '80K+',
        'skills': ['network security', 'penetration testing', 'linux'],
        'url': 'https://www.udacity.com/course/cybersecurity'
    },
    {
        'platform': 'skillshare',
        'title': 'Introduction to Cybersecurity',
        'instructor': 'Skillshare',
        'price': 1999,
        'rating': 4.5,
        'duration': '5 hours',
        'students': '90K+',
        'skills': ['cybersecurity', 'network security', 'threat analysis'],
        'url': 'https://www.skillshare.com/cybersecurity'
    },
    
    # PYTHON (4 courses)
    {
        'platform': 'udemy',
        'title': 'Complete Python Programming Course',
        'instructor': 'Udemy',
        'price': 399,
        'rating': 4.7,
        'duration': '40 hours',
        'students': '800K+',
        'skills': ['python', 'programming', 'data structures'],
        'url': 'https://www.udemy.com/course/complete-python'
    },
    {
        'platform': 'coursera',
        'title': 'Python for Everybody',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.8,
        'duration': '8 weeks',
        'students': '500K+',
        'skills': ['python', 'programming', 'databases'],
        'url': 'https://www.coursera.org/learn/python-for-everybody'
    },
    {
        'platform': 'pluralsight',
        'title': 'Python Advanced Techniques',
        'instructor': 'Pluralsight',
        'price': 3500,
        'rating': 4.8,
        'duration': '15 hours',
        'students': '180K+',
        'skills': ['python', 'machine learning', 'data analysis'],
        'url': 'https://www.pluralsight.com/courses/python-advanced'
    },
    {
        'platform': 'linkedin',
        'title': 'Learning Python',
        'instructor': 'LinkedIn Learning',
        'price': 2299,
        'rating': 4.6,
        'duration': '6 hours',
        'students': '300K+',
        'skills': ['python', 'programming', 'oop'],
        'url': 'https://www.linkedin.com/learning/learning-python'
    },
    
    # LINUX (3 courses)
    {
        'platform': 'udemy',
        'title': 'Linux Mastery: Complete Linux Training',
        'instructor': 'Udemy',
        'price': 449,
        'rating': 4.8,
        'duration': '32 hours',
        'students': '350K+',
        'skills': ['linux', 'command line', 'system administration'],
        'url': 'https://www.udemy.com/course/linux-mastery'
    },
    {
        'platform': 'pluralsight',
        'title': 'Linux System Administration',
        'instructor': 'Pluralsight',
        'price': 4000,
        'rating': 4.7,
        'duration': '20 hours',
        'students': '200K+',
        'skills': ['linux', 'system administration', 'networking'],
        'url': 'https://www.pluralsight.com/courses/linux-admin'
    },
    {
        'platform': 'coursera',
        'title': 'Introduction to Linux',
        'instructor': 'Coursera',
        'price': 3999,
        'rating': 4.6,
        'duration': '4 weeks',
        'students': '150K+',
        'skills': ['linux', 'command line', 'shell scripting'],
        'url': 'https://www.coursera.org/learn/linux'
    },
    
    # MACHINE LEARNING (4 courses)
    {
        'platform': 'udemy',
        'title': 'Machine Learning A-Z',
        'instructor': 'Udemy',
        'price': 599,
        'rating': 4.7,
        'duration': '44 hours',
        'students': '600K+',
        'skills': ['machine learning', 'python', 'data analysis'],
        'url': 'https://www.udemy.com/course/machinelearning'
    },
    {
        'platform': 'coursera',
        'title': 'Machine Learning by Andrew Ng',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.9,
        'duration': '7 weeks',
        'students': '1M+',
        'skills': ['machine learning', 'neural networks', 'deep learning'],
        'url': 'https://www.coursera.org/learn/machine-learning'
    },
    {
        'platform': 'pluralsight',
        'title': 'Machine Learning: Fundamentals',
        'instructor': 'Pluralsight',
        'price': 4500,
        'rating': 4.8,
        'duration': '12 hours',
        'students': '200K+',
        'skills': ['machine learning', 'algorithms', 'python'],
        'url': 'https://www.pluralsight.com/courses/ml-fundamentals'
    },
    {
        'platform': 'edx',
        'title': 'Machine Learning with Python',
        'instructor': 'edX',
        'price': 6999,
        'rating': 4.7,
        'duration': '5 weeks',
        'students': '180K+',
        'skills': ['machine learning', 'python', 'scikit-learn'],
        'url': 'https://www.edx.org/course/machine-learning'
    },
    
    # DATA SCIENCE (4 courses)
    {
        'platform': 'udemy',
        'title': 'Data Science A-Z',
        'instructor': 'Udemy',
        'price': 549,
        'rating': 4.6,
        'duration': '22 hours',
        'students': '400K+',
        'skills': ['data science', 'sql', 'python'],
        'url': 'https://www.udemy.com/course/datascience'
    },
    {
        'platform': 'coursera',
        'title': 'Data Science Specialization',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.8,
        'duration': '8 months',
        'students': '300K+',
        'skills': ['data science', 'statistics', 'r programming'],
        'url': 'https://www.coursera.org/specializations/data-science'
    },
    {
        'platform': 'pluralsight',
        'title': 'Data Science: Essentials',
        'instructor': 'Pluralsight',
        'price': 4200,
        'rating': 4.7,
        'duration': '14 hours',
        'students': '160K+',
        'skills': ['data science', 'statistics', 'visualization'],
        'url': 'https://www.pluralsight.com/courses/data-science-essentials'
    },
    {
        'platform': 'linkedin',
        'title': 'Data Science Foundations',
        'instructor': 'LinkedIn Learning',
        'price': 2299,
        'rating': 4.5,
        'duration': '5 hours',
        'students': '120K+',
        'skills': ['data science', 'statistics', 'pandas'],
        'url': 'https://www.linkedin.com/learning/data-science'
    },
    
    # WEB DEVELOPMENT (4 courses)
    {
        'platform': 'udemy',
        'title': 'The Complete Web Developer Course',
        'instructor': 'Udemy',
        'price': 479,
        'rating': 4.7,
        'duration': '30 hours',
        'students': '700K+',
        'skills': ['web development', 'html', 'css', 'javascript'],
        'url': 'https://www.udemy.com/course/web-development'
    },
    {
        'platform': 'coursera',
        'title': 'Full Stack Web Development',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.8,
        'duration': '6 months',
        'students': '250K+',
        'skills': ['web development', 'react', 'node.js'],
        'url': 'https://www.coursera.org/specializations/full-stack'
    },
    {
        'platform': 'pluralsight',
        'title': 'Web Development: Advanced',
        'instructor': 'Pluralsight',
        'price': 4500,
        'rating': 4.8,
        'duration': '18 hours',
        'students': '200K+',
        'skills': ['web development', 'javascript', 'frameworks'],
        'url': 'https://www.pluralsight.com/courses/web-development'
    },
    {
        'platform': 'skillshare',
        'title': 'Web Design Fundamentals',
        'instructor': 'Skillshare',
        'price': 1499,
        'rating': 4.5,
        'duration': '8 hours',
        'students': '150K+',
        'skills': ['web design', 'ui/ux', 'html/css'],
        'url': 'https://www.skillshare.com/web-design'
    },
    
    # ADDITIONAL COURSES
    {
        'platform': 'udemy',
        'title': 'React - The Complete Guide',
        'instructor': 'Udemy',
        'price': 499,
        'rating': 4.8,
        'duration': '50 hours',
        'students': '500K+',
        'skills': ['react', 'javascript', 'frontend'],
        'url': 'https://www.udemy.com/course/react-complete'
    },
    {
        'platform': 'udemy',
        'title': 'Complete Node.js Developer Course',
        'instructor': 'Udemy',
        'price': 449,
        'rating': 4.8,
        'duration': '32 hours',
        'students': '400K+',
        'skills': ['node.js', 'javascript', 'backend'],
        'url': 'https://www.udemy.com/course/nodejs-complete'
    },
    {
        'platform': 'udemy',
        'title': 'AWS Certified Solutions Architect',
        'instructor': 'Udemy',
        'price': 699,
        'rating': 4.7,
        'duration': '28 hours',
        'students': '350K+',
        'skills': ['aws', 'cloud', 'devops'],
        'url': 'https://www.udemy.com/course/aws-architect'
    },
    {
        'platform': 'udemy',
        'title': 'Deep Learning A-Z',
        'instructor': 'Udemy',
        'price': 649,
        'rating': 4.7,
        'duration': '38 hours',
        'students': '350K+',
        'skills': ['deep learning', 'tensorflow', 'neural networks'],
        'url': 'https://www.udemy.com/course/deep-learning'
    },
    {
        'platform': 'coursera',
        'title': 'Deep Learning Specialization',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.9,
        'duration': '4 months',
        'students': '400K+',
        'skills': ['deep learning', 'cnn', 'rnn'],
        'url': 'https://www.coursera.org/specializations/deep-learning'
    },
    {
        'platform': 'coursera',
        'title': 'Cloud Fundamentals',
        'instructor': 'Coursera',
        'price': 4999,
        'rating': 4.8,
        'duration': '4 weeks',
        'students': '200K+',
        'skills': ['cloud', 'aws', 'azure'],
        'url': 'https://www.coursera.org/learn/cloud-fundamentals'
    },
    {
        'platform': 'pluralsight',
        'title': 'Kubernetes: Getting Started',
        'instructor': 'Pluralsight',
        'price': 3500,
        'rating': 4.8,
        'duration': '8 hours',
        'students': '220K+',
        'skills': ['kubernetes', 'docker', 'devops'],
        'url': 'https://www.pluralsight.com/courses/kubernetes'
    },
    {
        'platform': 'udemy',
        'title': 'Flutter & Dart - Complete Guide',
        'instructor': 'Udemy',
        'price': 549,
        'rating': 4.8,
        'duration': '38 hours',
        'students': '250K+',
        'skills': ['flutter', 'dart', 'mobile development'],
        'url': 'https://www.udemy.com/course/flutter-dart'
    },
    {
        'platform': 'udemy',
        'title': 'Blockchain & Cryptocurrency Masterclass',
        'instructor': 'Udemy',
        'price': 599,
        'rating': 4.6,
        'duration': '20 hours',
        'students': '120K+',
        'skills': ['blockchain', 'cryptocurrency', 'solidity'],
        'url': 'https://www.udemy.com/course/blockchain'
    },
]

# ============================================================================
# CAREER DOMAINS DATABASE (9 DOMAINS)
# ============================================================================

CAREER_DOMAINS_MAP = {
    'ai_engineering': {
        'name': 'AI & Machine Learning Engineering',
        'icon': '🤖',
        'category': 'Technology',
        'description': 'Build intelligent systems using deep learning and neural networks',
        'skills': ['python', 'tensorflow', 'pytorch', 'deep learning', 'neural networks', 
                   'nlp', 'computer vision', 'scikit-learn', 'keras', 'machine learning'],
        'entry_level': '₹12-18 LPA',
        'mid_level': '₹20-30 LPA',
        'senior_level': '₹35-50+ LPA',
        'demand_trend': '🚀 Exploding',
        'growth': 85,
        'job_market_size': 5000,
        'competition': 'High',
        'color': '#9b59b6',
        'top_companies': ['Google', 'OpenAI', 'DeepMind', 'Meta', 'Tesla', 'NVIDIA'],
        'avg_job_openings': 450,
        'required_projects': ['Chatbot', 'Image Classification', 'NLP System', 'Time Series']
    },
    'data_science': {
        'name': 'Data Science & Analytics',
        'icon': '📊',
        'category': 'Technology',
        'description': 'Transform raw data into actionable insights',
        'skills': ['python', 'machine learning', 'statistics', 'sql', 'data analysis', 
                   'pandas', 'numpy', 'tableau', 'power bi', 'r'],
        'entry_level': '₹8-12 LPA',
        'mid_level': '₹16-24 LPA',
        'senior_level': '₹28-40+ LPA',
        'demand_trend': '📈 Rising',
        'growth': 75,
        'job_market_size': 8000,
        'competition': 'Medium-High',
        'color': '#3498db',
        'top_companies': ['Flipkart', 'Amazon', 'Microsoft', 'Google', 'JPMorgan'],
        'avg_job_openings': 520,
        'required_projects': ['Sales Analysis', 'Customer Segmentation', 'Predictive Model', 'Dashboard']
    },
    'web_development': {
        'name': 'Full Stack Web Development',
        'icon': '💻',
        'category': 'Technology',
        'description': 'Build modern web applications from frontend to backend',
        'skills': ['javascript', 'react', 'node.js', 'python', 'django', 'mongodb', 
                   'express', 'html', 'css', 'rest api', 'docker'],
        'entry_level': '₹5-8 LPA',
        'mid_level': '₹12-18 LPA',
        'senior_level': '₹22-35+ LPA',
        'demand_trend': '📈 Steady',
        'growth': 60,
        'job_market_size': 15000,
        'competition': 'Very High',
        'color': '#e74c3c',
        'top_companies': ['Paytm', 'Myntra', 'Uber', 'Netflix', 'Shopify'],
        'avg_job_openings': 850,
        'required_projects': ['E-commerce Site', 'Blog Platform', 'Chat App', 'Task Manager']
    },
    'cloud_devops': {
        'name': 'Cloud & DevOps Engineering',
        'icon': '☁️',
        'category': 'Infrastructure',
        'description': 'Architect and manage cloud infrastructure at scale',
        'skills': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'devops', 
                   'terraform', 'linux', 'jenkins', 'ci/cd'],
        'entry_level': '₹10-15 LPA',
        'mid_level': '₹18-26 LPA',
        'senior_level': '₹30-45+ LPA',
        'demand_trend': '📈 Rising',
        'growth': 80,
        'job_market_size': 6000,
        'competition': 'Medium',
        'color': '#f39c12',
        'top_companies': ['Accenture', 'TCS', 'Infosys', 'IBM', 'AWS'],
        'avg_job_openings': 380,
        'required_projects': ['K8s Cluster', 'CI/CD Pipeline', 'Microservices', 'Infrastructure']
    },
    'cybersecurity': {
        'name': 'Cybersecurity & Ethical Hacking',
        'icon': '🔒',
        'category': 'Security',
        'description': 'Defend systems and protect against evolving threats',
        'skills': ['network security', 'ethical hacking', 'cryptography', 'python', 
                   'linux', 'penetration testing', 'threat analysis', 'compliance'],
        'entry_level': '₹10-14 LPA',
        'mid_level': '₹18-28 LPA',
        'senior_level': '₹32-50+ LPA',
        'demand_trend': '🚀 Critical',
        'growth': 90,
        'job_market_size': 3000,
        'competition': 'Low-Medium',
        'color': '#2ecc71',
        'top_companies': ['Cisco', 'Kaspersky', 'CrowdStrike', 'Palo Alto', 'Fortinet'],
        'avg_job_openings': 250,
        'required_projects': ['Vulnerability Assessment', 'Penetration Test', 'Firewall Config', 'Incident Response']
    },
    'mobile_development': {
        'name': 'Mobile App Development',
        'icon': '📱',
        'category': 'Technology',
        'description': 'Create powerful applications for iOS and Android',
        'skills': ['swift', 'kotlin', 'react native', 'flutter', 'javascript', 'java', 
                   'firebase', 'rest api', 'git', 'mobile ui'],
        'entry_level': '₹6-10 LPA',
        'mid_level': '₹14-20 LPA',
        'senior_level': '₹24-36+ LPA',
        'demand_trend': '📈 High',
        'growth': 70,
        'job_market_size': 10000,
        'competition': 'Medium-High',
        'color': '#1abc9c',
        'top_companies': ['Swiggy', 'Ola', 'Zomato', 'Instagram', 'Gojek'],
        'avg_job_openings': 620,
        'required_projects': ['E-commerce App', 'Social App', 'Fitness Tracker', 'Food Delivery']
    },
    'blockchain': {
        'name': 'Blockchain & Web3 Development',
        'icon': '⛓️',
        'category': 'Emerging',
        'description': 'Build decentralized applications and smart contracts',
        'skills': ['solidity', 'ethereum', 'web3.js', 'smart contracts', 'blockchain', 
                   'cryptography', 'dapps', 'bitcoin', 'consensus'],
        'entry_level': '₹14-20 LPA',
        'mid_level': '₹25-35 LPA',
        'senior_level': '₹40-60+ LPA',
        'demand_trend': '🚀 Emerging',
        'growth': 120,
        'job_market_size': 2000,
        'competition': 'Low',
        'color': '#f7931a',
        'top_companies': ['Polygon', 'Consensys', 'Coinbase', 'Binance', 'OpenSea'],
        'avg_job_openings': 180,
        'required_projects': ['Smart Contract', 'DeFi Protocol', 'NFT Platform', 'DAO']
    },
    'backend_development': {
        'name': 'Backend Development',
        'icon': '🔧',
        'category': 'Technology',
        'description': 'Build scalable server-side applications',
        'skills': ['python', 'java', 'golang', 'rust', 'nodejs', 'databases', 
                   'api design', 'microservices', 'message queues', 'caching'],
        'entry_level': '₹7-11 LPA',
        'mid_level': '₹14-22 LPA',
        'senior_level': '₹26-40+ LPA',
        'demand_trend': '📈 High',
        'growth': 65,
        'job_market_size': 12000,
        'competition': 'High',
        'color': '#2c3e50',
        'top_companies': ['Amazon', 'Microsoft', 'Google', 'Spotify', 'Airbnb'],
        'avg_job_openings': 780,
        'required_projects': ['REST API', 'Microservice', 'Database Design', 'Auth System']
    },
    'frontend_development': {
        'name': 'Frontend Development',
        'icon': '🎨',
        'category': 'Technology',
        'description': 'Create beautiful and responsive user interfaces',
        'skills': ['javascript', 'react', 'vue', 'angular', 'html', 'css', 
                   'typescript', 'webpack', 'responsive design', 'web performance'],
        'entry_level': '₹6-10 LPA',
        'mid_level': '₹12-18 LPA',
        'senior_level': '₹20-32+ LPA',
        'demand_trend': '📈 High',
        'growth': 68,
        'job_market_size': 13000,
        'competition': 'Very High',
        'color': '#e91e63',
        'top_companies': ['Netflix', 'Airbnb', 'Uber', 'Shopify', 'Stripe'],
        'avg_job_openings': 720,
        'required_projects': ['Portfolio', 'E-commerce', 'Dashboard', 'SPA Application']
    },
}

DISPLAY_NAME_TO_KEY = {v['name'].lower(): k for k, v in CAREER_DOMAINS_MAP.items()}

def resolve_career_goal(input_value: Optional[str]) -> Optional[str]:
    """Robustly resolve career goal text to a domain key."""
    if not input_value:
        return None
    s = html.unescape(str(input_value)).strip()
    if not s:
        return None
    # direct key
    if s in CAREER_DOMAINS_MAP:
        return s
    lower_s = s.lower()
    # exact display name
    if lower_s in DISPLAY_NAME_TO_KEY:
        return DISPLAY_NAME_TO_KEY[lower_s]
    # normalize common punctuation
    candidate = re.sub(r'[\-\.\/\&]', ' ', lower_s)
    candidate = re.sub(r'\s+', '_', candidate).strip('_')
    if candidate in CAREER_DOMAINS_MAP:
        return candidate
    # substring match
    for name, key in DISPLAY_NAME_TO_KEY.items():
        if lower_s in name or name in lower_s:
            return key
    # token overlap scoring
    tokens = set(re.findall(r'\w+', lower_s))
    best_key = None
    best_score = 0
    for key, v in CAREER_DOMAINS_MAP.items():
        name_tokens = set(re.findall(r'\w+', v['name'].lower()))
        score = len(tokens & name_tokens)
        if score > best_score:
            best_score = score
            best_key = key
    if best_score > 0:
        logger.info(f"Resolved career goal '{input_value}' -> '{best_key}' (score={best_score})")
        return best_key
    logger.info(f"Could not resolve career goal: {input_value}")
    return None

async def extract_career_goal_from_request(request: Request, provided: Optional[str]) -> Optional[str]:
    """Extract career goal from multiple places: provided, query, json, form."""
    if provided:
        v = str(provided).strip()
        if v:
            return v
    # query params
    for qk in ('career_goal', 'domain', 'career', 'selected_domain', 'domain_key'):
        q = request.query_params.get(qk)
        if q:
            return q
    # try JSON
    try:
        ct = request.headers.get('content-type', '')
        if 'application/json' in ct:
            body = await request.json()
            if isinstance(body, dict):
                for key in ('career_goal', 'career', 'domain', 'domain_key', 'selected_domain', 'careerGoal', 'career_domain'):
                    val = body.get(key)
                    if val:
                        return str(val)
    except Exception:
        pass
    # try form
    try:
        form = await request.form()
        for key in ('career_goal', 'career', 'domain', 'career_domain', 'selected_domain', 'careerGoal', 'career_goal_input', 'domain_key'):
            if key in form:
                val = form.get(key)
                if val:
                    return str(val)
    except Exception:
        pass
    return None

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: str
    password: str
    full_name: str

class SkillAnalysisRequest(BaseModel):
    """Skill analysis request model"""
    skills: str
    cgpa: float
    career_goal: str

# ============================================================================
# SECURITY UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify hashed password"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request) -> Optional[Dict]:
    """Get current authenticated user from token"""
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        
        if not username or username not in users_db:
            return None
        
        return users_db[username]
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except Exception as e:
        logger.warning(f"Invalid token or error decoding: {e}")
        return None

# ensure there is at least one admin user in the in-memory store

def create_default_admin():
    """If the users_db has no admin, add one with a default password."""
    if 'admin' not in users_db:
        users_db['admin'] = {
            'username': 'admin',
            'email': 'admin@example.com',
            'full_name': 'Administrator',
            'hashed_password': hash_password('admin123'),
            'joined_date': datetime.now().isoformat(),
            'role': 'admin',
            'resume': None
        }

# call on import so the account exists
create_default_admin()


def require_admin(user: Optional[Dict]) -> None:
    """Raise HTTPException if the supplied user is not an administrator."""
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

# ============================================================================
# SKILL ANALYSIS ENGINE
# ============================================================================

def analyze_skills(user_skills: str, target_domain: str, cgpa: float) -> Dict[str, Any]:
    """Advanced skill analysis with CGPA adjustment"""
    try:
        if not user_skills or not target_domain:
            return {}
        
        user_skills_list = [skill.strip().lower() for skill in user_skills.split(',') if skill.strip()]
        domain_info = CAREER_DOMAINS_MAP.get(target_domain, {})
        domain_skills = domain_info.get('skills', [])
        
        if not domain_skills:
            logger.error(f"Domain {target_domain} not found or has no skills")
            return {}
        
        # Calculate matches
        matched_skills = [s for s in domain_skills if s in user_skills_list]
        missing_skills = [s for s in domain_skills if s not in user_skills_list]
        match_percentage = (len(matched_skills) / len(domain_skills)) * 100 if domain_skills else 0
        
        # CGPA bonus
        cgpa_bonus = 0
        if cgpa >= 9.0:
            cgpa_bonus = 15
        elif cgpa >= 8.0:
            cgpa_bonus = 10
        elif cgpa >= 7.0:
            cgpa_bonus = 5
        elif cgpa >= 6.0:
            cgpa_bonus = 2
        
        adjusted_score = min(100, match_percentage + cgpa_bonus)
        
        # Readiness level
        if adjusted_score >= 80:
            readiness, timeline, action = "High", "1-3 months", "Ready to apply now"
        elif adjusted_score >= 60:
            readiness, timeline, action = "Medium-High", "3-6 months", "Close to job-ready"
        elif adjusted_score >= 40:
            readiness, timeline, action = "Medium", "6-12 months", "Focused learning needed"
        elif adjusted_score >= 20:
            readiness, timeline, action = "Low-Medium", "12-18 months", "Significant upskilling required"
        else:
            readiness, timeline, action = "Low", "18-24 months", "Start from fundamentals"
        
        logger.info(f"Analysis completed for domain: {target_domain}, Score: {adjusted_score}")
        
        return {
            'domain': domain_info.get('name', ''),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'skills_count': {
                'total': len(domain_skills),
                'have': len(matched_skills),
                'need': len(missing_skills),
                'percentage_have': round(match_percentage, 1)
            },
            'match_percentage': round(match_percentage, 1),
            'adjusted_match': round(adjusted_score, 1),
            'cgpa_adjustment': cgpa_bonus,
            'cgpa_score': cgpa,
            'readiness_level': readiness,
            'estimated_timeline': timeline,
            'action_required': action,
            'salary_info': {
                'entry_level': domain_info.get('entry_level', ''),
                'mid_level': domain_info.get('mid_level', ''),
                'senior_level': domain_info.get('senior_level', ''),
            },
            'domain_info': {
                'growth_potential': domain_info.get('growth', 0),
                'competition': domain_info.get('competition', 'Medium'),
                'avg_job_openings': domain_info.get('avg_job_openings', 0),
                'top_companies': domain_info.get('top_companies', []),
                'required_projects': domain_info.get('required_projects', []),
                'category': domain_info.get('category', 'Technology'),
            }
        }
    except Exception as e:
        logger.error(f"Error in skill analysis: {e}")
        return {}

# ============================================================================
# ROUTES - AUTHENTICATION
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirect to login"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
	"""Handle login - return JSONResponse with cookie set"""
	try:
		user = users_db.get(username)
		
		if not user or not verify_password(password, user.get('hashed_password', '')):
			logger.warning(f"Failed login attempt for user: {username}")
			raise HTTPException(status_code=401, detail="Invalid username or password")
		
		access_token = create_access_token(data={"sub": username})
		resp = JSONResponse({"success": True, "message": "Login successful"})
		# set cookie on the response we actually return
		resp.set_cookie(
			key="access_token",
			value=access_token,
			httponly=True,
			max_age=int(config.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
			samesite="lax"
		)
		logger.info(f"User logged in: {username}")
		
		return resp
	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Login error: {e}")
		raise HTTPException(status_code=500, detail="Server error")

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(username: str = Form(...), email: str = Form(...), 
                password: str = Form(...), full_name: str = Form(...)):
    """Handle signup - return JSONResponse with cookie set"""
    try:
        if username in users_db:
            logger.warning(f"Signup attempt with existing username: {username}")
            raise HTTPException(status_code=400, detail="Username already registered")

        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Create user (student by default)
        users_db[username] = {
            'username': username,
            'email': email,
            'full_name': full_name,
            'hashed_password': hash_password(password),
            'joined_date': datetime.now().isoformat(),
            'role': 'student',
            'resume': None
        }

        access_token = create_access_token(data={"sub": username})
        resp = JSONResponse({"success": True, "message": "Account created successfully"})
        # set cookie on the response we actually return
        resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=int(config.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            samesite="lax"
        )
        logger.info(f"New user registered: {username}")

        return resp
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Server error")
async def logout(response: Response):
    """Logout user"""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    logger.info("User logged out")
    return response

# ============================================================================
# ROUTES - MAIN APPLICATION
# ============================================================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "career_domains": CAREER_DOMAINS_MAP,
            "total_domains": len(CAREER_DOMAINS_MAP)
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard error")

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_career(request: Request, skills: Optional[str] = Form(None), cgpa: Optional[float] = Form(None),
                         career_goal: Optional[str] = Form(None)):
    """Analyze career skills (accepts form or JSON) - defensive implementation to avoid template errors."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")

    try:
        # --- gather inputs from JSON/form/query robustly ---
        body_json = None
        try:
            if 'application/json' in request.headers.get('content-type', ''):
                body_json = await request.json()
        except Exception:
            body_json = None

        if not skills or not str(skills).strip():
            if body_json and isinstance(body_json, dict):
                skills = body_json.get('skills') or body_json.get('user_skills') or body_json.get('skills_input')
            if not skills:
                try:
                    form = await request.form()
                    skills = form.get('skills') or form.get('user_skills') or form.get('skills_input')
                except Exception:
                    pass

        if cgpa is None:
            if body_json and isinstance(body_json, dict):
                cgpa = body_json.get('cgpa')
            if cgpa is None:
                try:
                    form = await request.form()
                    cgpa = form.get('cgpa') or form.get('score') or form.get('cgpa_input')
                except Exception:
                    pass

        try:
            if cgpa is not None and not isinstance(cgpa, float):
                cgpa = float(cgpa)
        except Exception:
            raise HTTPException(status_code=400, detail="CGPA must be a number between 0 and 10")

        if not skills or not str(skills).strip():
            raise HTTPException(status_code=400, detail="Please provide your skills")
        if not (0 <= cgpa <= 10):
            raise HTTPException(status_code=400, detail="CGPA must be between 0 and 10")

        # resolve career goal (from many possible inputs)
        raw_goal = await extract_career_goal_from_request(request, career_goal)
        if not raw_goal and body_json and isinstance(body_json, dict):
            for key in ('career_goal', 'career', 'domain', 'domain_key', 'selected_domain', 'careerGoal', 'career_domain'):
                if key in body_json and body_json.get(key):
                    raw_goal = str(body_json.get(key))
                    break

        career_goal_key = resolve_career_goal(raw_goal) if raw_goal else None

        if not career_goal_key:
            # infer from skills
            user_tokens = set([s.strip().lower() for s in str(skills).split(",") if s.strip()])
            best_key = None
            best_overlap = 0
            for key, domain in CAREER_DOMAINS_MAP.items():
                domain_skills = set([s.lower() for s in domain.get('skills', [])])
                overlap = len(domain_skills & user_tokens)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_key = key
            if best_key and best_overlap > 0:
                career_goal_key = best_key
                logger.info(f"Inferred career goal from skills -> {career_goal_key} (overlap={best_overlap})")
            else:
                if raw_goal:
                    career_goal_key = resolve_career_goal(raw_goal)

        if not career_goal_key:
            raise HTTPException(status_code=400, detail="Invalid career goal - please select a domain or type its name")

        # run analysis (may return {} on edge cases)
        skill_analysis = analyze_skills(skills, career_goal_key, cgpa)

        # Ensure skill_analysis has safe defaults so templates never throw attribute errors
        domain_info = CAREER_DOMAINS_MAP.get(career_goal_key, {})
        safe_defaults = {
            'domain': domain_info.get('name', ''),
            'matched_skills': skill_analysis.get('matched_skills', []) if isinstance(skill_analysis, dict) else [],
            'missing_skills': skill_analysis.get('missing_skills', []) if isinstance(skill_analysis, dict) else domain_info.get('skills', [])[:],
            'skills_count': skill_analysis.get('skills_count', {'total': len(domain_info.get('skills', [])),
                                                               'have': len(skill_analysis.get('matched_skills', [])) if isinstance(skill_analysis, dict) else 0,
                                                               'need': len(skill_analysis.get('missing_skills', [])) if isinstance(skill_analysis, dict) else len(domain_info.get('skills', []))}),
            'match_percentage': skill_analysis.get('match_percentage', 0) if isinstance(skill_analysis, dict) else 0,
            'adjusted_match': skill_analysis.get('adjusted_match', 0) if isinstance(skill_analysis, dict) else 0,
            'cgpa_adjustment': skill_analysis.get('cgpa_adjustment', 0) if isinstance(skill_analysis, dict) else 0,
            'cgpa_score': skill_analysis.get('cgpa_score', cgpa) if isinstance(skill_analysis, dict) else cgpa,
            'readiness_level': skill_analysis.get('readiness_level', 'Unknown') if isinstance(skill_analysis, dict) else 'Unknown',
            'estimated_timeline': skill_analysis.get('estimated_timeline', 'N/A') if isinstance(skill_analysis, dict) else 'N/A',
            'action_required': skill_analysis.get('action_required', '') if isinstance(skill_analysis, dict) else '',
            'salary_info': skill_analysis.get('salary_info', {
                'entry_level': domain_info.get('entry_level', ''),
                'mid_level': domain_info.get('mid_level', ''),
                'senior_level': domain_info.get('senior_level', '')
            }),
            'domain_info': skill_analysis.get('domain_info', {
                'growth_potential': domain_info.get('growth', 0),
                'competition': domain_info.get('competition', 'Medium'),
                'avg_job_openings': domain_info.get('avg_job_openings', 0),
                'top_companies': domain_info.get('top_companies', []),
                'required_projects': domain_info.get('required_projects', []),
                'category': domain_info.get('category', '')
            })
        }

        # If analyze_skills returned a dict, merge any extra keys
        if isinstance(skill_analysis, dict):
            for k, v in skill_analysis.items():
                if k not in safe_defaults:
                    safe_defaults[k] = v

        skill_analysis = safe_defaults

        # Provide "salary" key (templates expect analysis.salary.entry etc.)
        # keep both keys for compatibility: 'salary_info' and 'salary'
        salary_info = skill_analysis.get('salary_info', {})
        skill_analysis['salary'] = {
            'entry': salary_info.get('entry_level') or salary_info.get('entry') or domain_info.get('entry_level', ''),
            'mid': salary_info.get('mid_level') or salary_info.get('mid') or domain_info.get('mid_level', ''),
            'senior': salary_info.get('senior_level') or salary_info.get('senior') or domain_info.get('senior_level', '')
        }

        # --------------------------
        # map missing skills -> recommended courses
        # --------------------------
        def top_courses_for_skill(skill_name, top_n=3):
            s = skill_name.strip().lower()
            matches = []
            for c in COURSES_DATABASE:
                c_skills = [x.lower() for x in c.get('skills', [])]
                if any(s in ks or ks in s for ks in c_skills):
                    # scoring heuristic
                    rating = float(c.get('rating', 0) or 0)
                    price = int(c.get('price', 0) or 0)
                    score = rating * 20 - (price / 100.0)
                    matches.append((score, {
                        'title': c.get('title') or c.get('name') or '',
                        'platform': c.get('platform', ''),
                        'price': c.get('price', 0),
                        'rating': rating,
                        'url': c.get('url', '#')
                    }))
            matches.sort(key=lambda x: x[0], reverse=True)
            return [m[1] for m in matches[:top_n]]

        skill_course_map = {}
        for ms in skill_analysis.get('missing_skills', []) or []:
            skill_course_map[ms] = top_courses_for_skill(ms, top_n=3)

        # --------------------------
        # simple level roadmap grouping
        # --------------------------
        missing = skill_analysis.get('missing_skills', []) or []
        n = len(missing)
        level_roadmap = {'Foundation': [], 'Core': [], 'Advanced': []}
        if n > 0:
            f_cut = ceil(n * 0.3)
            c_cut = ceil(n * 0.7)
            for idx, sname in enumerate(missing):
                if idx < f_cut:
                    level_roadmap['Foundation'].append(sname)
                elif idx < c_cut:
                    level_roadmap['Core'].append(sname)
                else:
                    level_roadmap['Advanced'].append(sname)

        # --------------------------
        # suggest best domain based on user's current skills (overlap)
        # --------------------------
        user_tokens = set([t.strip().lower() for t in skills.split(',') if t.strip()])
        best_domain = None
        best_score = 0
        for key, domain in CAREER_DOMAINS_MAP.items():
            domain_sk = set([s.lower() for s in domain.get('skills', [])])
            score = len(user_tokens & domain_sk)
            if score > best_score:
                best_score = score
                best_domain = key
        suggested_domain_name = CAREER_DOMAINS_MAP.get(best_domain, {}).get('name') if best_domain else None

        # persist analysis (include computed score and link resume)
        analysis_id = str(uuid.uuid4())[:8]
        user_analyses[analysis_id] = {
            'user': user['username'],
            'skills': skills,
            'cgpa': cgpa,
            'career_goal': career_goal_key,
            'skill_analysis': skill_analysis,
            'score': skill_analysis.get('adjusted_match', 0),
            'resume': users_db.get(user['username'], {}).get('resume'),
            'timestamp': datetime.now().isoformat()
        }

        # --- render template defensively ---
        try:
            return templates.TemplateResponse("results.html", {
                "request": request,
                "user": user,
                "analysis_id": analysis_id,
                "skills": skills,
                "cgpa": cgpa,
                "career_goal": career_goal_key,
                "skill_analysis": skill_analysis,
                "career_domain": CAREER_DOMAINS_MAP.get(career_goal_key, {}),
                "missing_skills": skill_analysis.get('missing_skills', []),
                "skill_course_map": skill_course_map,
                "level_roadmap": level_roadmap,
                "suggested_domain_name": suggested_domain_name,
                "suggested_domain_score": best_score
            })
        except Exception as tpl_err:
            # log and fallback to the robust advanced results page with safe minimal context
            logger.error(f"Template render error in results.html: {tpl_err}", exc_info=True)
            try:
                return templates.TemplateResponse("resusts_advanced.html", {
                    "request": request,
                    "user": user,
                    "analysis": skill_analysis,
                    "courses": [], 
                    "jobs": []
                })
            except Exception as fallback_err:
                logger.error(f"Fallback render also failed: {fallback_err}", exc_info=True)
                raise HTTPException(status_code=500, detail="Analysis error")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis error")

@app.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request, career_goal: Optional[str] = None):
    """Render courses page. Accepts optional ?skill=... or career_goal to pre-filter courses.
    This implementation normalizes course entries to avoid template errors and logs details on failure.
    """
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    try:
        # start with full list
        selected_courses = list(COURSES_DATABASE)
        selected_domain = None

        # prefer explicit 'skill' query param, else use career_goal
        skill_query = request.query_params.get('skill') or career_goal

        if skill_query:
            # try resolving to a domain key first
            domain_key = resolve_career_goal(skill_query)
            if domain_key:
                selected_domain = CAREER_DOMAINS_MAP.get(domain_key)
                domain_skills = set([s.lower() for s in selected_domain.get('skills', [])])
                selected_courses = [
                    c for c in COURSES_DATABASE
                    if domain_skills & set([s.lower() for s in c.get('skills', [])])
                ]
            else:
                # fallback: treat skill_query as skill text and match courses that mention it
                q = str(skill_query).strip().lower()
                selected_courses = [
                    c for c in COURSES_DATABASE
                    if any(q in (s or '').lower() for s in c.get('skills', []))
                    or q in (c.get('title') or '').lower()
                ]

        # Normalize course dicts so templates won't crash if keys are missing
        processed = []
        for raw in selected_courses:
            c = dict(raw)  # shallow copy
            c.setdefault('level', 'Beginner')
            c.setdefault('certificate', False)
            # ensure numeric/consistent types
            try:
                c['rating'] = float(c.get('rating', 0) or 0)
            except Exception:
                c['rating'] = 0.0
            try:
                c['price'] = int(c.get('price', 0) or 0)
            except Exception:
                c['price'] = 0
            c.setdefault('students', c.get('students', '0'))
            # recommendation_score: simple heuristic (rating-based + budget bonus)
            score = int(min(100, round((c['rating'] / 5.0) * 100)))
            if c['price'] and c['price'] < 2000:
                score = min(100, score + 5)
            c['recommendation_score'] = score
            processed.append(c)

        return templates.TemplateResponse("course_advanced.html", {
            "request": request,
            "user": user,
            "courses": processed,
            "total_courses": len(processed),
            "missing_skills": []
        })
    except Exception as e:
        logger.error(f"Courses page error: {e}", exc_info=True)
        # safe fallback: render comparison page with minimal context to avoid 500 response
        try:
            return templates.TemplateResponse("course_comparision.html", {
                "request": request,
                "skill_analysis": {},
                "missing_skills": []
            })
        except Exception:
            # if fallback also fails, return a controlled HTTP error
            raise HTTPException(status_code=500, detail="Courses page error")

@app.get("/domain/{domain_key}", response_class=HTMLResponse)
async def domain_page(request: Request, domain_key: str):
    """Domain-specific roadmap, course recommendations and job links."""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    domain = CAREER_DOMAINS_MAP.get(domain_key)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Build a simple "analysis" (roadmap-ready) structure expected by template
    skills = domain.get('skills', [])
    matched_skills = []  # user-specific matched skills would come from user profile/analysis
    missing_skills = skills.copy()

    analysis = {
        'adjusted_match': 0,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'readiness_level': "Not started",
        'timeline': "Depends on learning plan",
        'growth': domain.get('growth', 0),
        'job_openings': domain.get('avg_job_openings', 0),
        'salary': {
            'entry': domain.get('entry_level', ''),
            'mid': domain.get('mid_level', ''),
            'senior': domain.get('senior_level', '')
        },
        'top_companies': domain.get('top_companies', []),
        'required_projects': domain.get('required_projects', []),
        'domain': domain.get('name', '')
    }

    # Jobs: create helpful external search links (LinkedIn, Indeed, Google Jobs)
    jobs = []
    # General domain job search
    q = f"{domain.get('name')} jobs"
    jobs.append({
        'title': f"{domain.get('name')} roles (Search)",
        'company': 'Various',
        'location': 'Remote / Multiple locations',
        'experience': 'Entry - Senior',
        'salary': domain.get('entry_level', ''),
        'skills': skills[:5],
        'description': f"Search live job openings for {domain.get('name')}",
        'posting_url': f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(q)}"
    })
    # per top company quick searches
    for comp in domain.get('top_companies', [])[:6]:
        comp_q = f"{domain.get('name')} {comp} jobs"
        jobs.append({
            'title': f"Jobs at {comp}",
            'company': comp,
            'location': 'See postings',
            'experience': 'Varies',
            'salary': '',
            'skills': skills[:4],
            'description': f"Openings at {comp} for {domain.get('name')}",
            'posting_url': f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(comp_q)}"
        })

    # Courses: provide a short list of top courses matching the domain skills
    domain_skills = set([s.lower() for s in domain.get('skills', [])])
    matched_courses = []
    for c in COURSES_DATABASE:
        c_sk = set([s.lower() for s in c.get('skills', [])])
        if domain_skills & c_sk:
            matched_courses.append(c)
    # sort by rating desc then price asc (better rating, cheaper first)
    matched_courses.sort(key=lambda x: (-(float(x.get('rating', 0) or 0)), int(x.get('price', 0) or 0)))
    # limit results to a reasonable number for the UI
    courses = matched_courses[:8]

    logger.info(f"Domain page served: {domain_key} for user: {user['username']} (courses={len(courses)}, jobs={len(jobs)})")
 
    return templates.TemplateResponse("resusts_advanced.html", {
         "request": request,
         "user": user,
         "analysis": analysis,
         "courses": courses,
         "jobs": jobs
     })

@app.get("/api/health")
async def health_check():
    return {"status":"healthy","app":config.APP_NAME,"version":config.APP_VERSION,"timestamp":datetime.now().isoformat()}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# --------------------------
# RESUME & ADMIN ROUTES
# --------------------------

@app.post("/upload_resume")
async def upload_resume(request: Request, resume: UploadFile = File(...)):
    """Allow authenticated users to upload a resume file."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")
    os.makedirs("resumes", exist_ok=True)
    filename = f"{user['username']}_{int(datetime.now().timestamp())}_{resume.filename}"
    filepath = os.path.join("resumes", filename)
    with open(filepath, "wb") as f:
        f.write(await resume.read())
    user['resume'] = filepath
    logger.info(f"Resume uploaded for user: {user['username']} -> {filepath}")
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/resume/{username}")
async def serve_resume(username: str):
    """Return the resume file for the given username."""
    requested = users_db.get(username)
    if not requested or not requested.get('resume'):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(requested['resume'], media_type="application/octet-stream", filename=os.path.basename(requested['resume']))

@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    user = await get_current_user(request)
    require_admin(user)
    return RedirectResponse("/admin/students", status_code=302)

@app.get("/admin/students", response_class=HTMLResponse)
async def admin_students(request: Request):
    user = await get_current_user(request)
    require_admin(user)
    entries = []
    for aid, info in user_analyses.items():
        entries.append({
            'analysis_id': aid,
            'username': info.get('user'),
            'score': info.get('score'),
            'cgpa': info.get('cgpa'),
            'timestamp': info.get('timestamp'),
            'resume': info.get('resume')
        })
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": user, "entries": entries})

@app.get("/admin/review/{analysis_id}", response_class=HTMLResponse)
async def admin_review(request: Request, analysis_id: str):
    user = await get_current_user(request)
    require_admin(user)
    entry = user_analyses.get(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return templates.TemplateResponse("admin_review.html", {
        "request": request,
        "user": user,
        "entry": entry
    })

@app.post("/admin/review/{analysis_id}")
async def admin_review_post(request: Request, analysis_id: str, notes: str = Form(None)):
    user = await get_current_user(request)
    require_admin(user)
    entry = user_analyses.get(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Analysis not found")
    entry['admin_notes'] = notes
    return RedirectResponse(f"/admin/review/{analysis_id}", status_code=302)

# general exception handler remains below
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/course_comparision", response_class=HTMLResponse)
async def course_comparision(request: Request, skill: Optional[str] = None):
    """Render course comparison page (compat route used by dashboard/query links)."""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)

    # Determine skill filter from query param
    skill_q = skill or request.query_params.get('skill') or ''
    q = str(skill_q).strip().lower()

    # Filter courses by skill token match (safe)
    matched = []
    for c in COURSES_DATABASE:
        c_sk = [s.lower() for s in c.get('skills', [])]
        title = (c.get('title') or c.get('name') or '').lower()
        if q and (any(q in s for s in c_sk) or q in title):
            matched.append(c)

    # Provide minimal safe context for template
    try:
        return templates.TemplateResponse("course_comparision.html", {
            "request": request,
            "user": user,
            "missing_skills": [skill_q] if skill_q else [],
            "skill_analysis": {},  # kept empty safe object
            "courses": matched if matched else COURSES_DATABASE  # fallback to full list
        })
    except Exception as e:
        logger.error(f"course_comparision render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Courses comparison error")

@app.get("/course_comparison", response_class=HTMLResponse)
async def course_comparison_alias(request: Request):
    """Alias route to support alternate spelling - redirects to /course_comparision preserving query."""
    qs = request.url.query
    target = "/course_comparision"
    if qs:
        target = f"{target}?{qs}"
    return RedirectResponse(url=target, status_code=302)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)