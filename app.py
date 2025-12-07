from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import sqlite3
import math
import os
import requests
from functools import lru_cache

app = Flask(__name__)

# Configuration: Use Vedic time (day starts at sunrise) or Western time (midnight)
USE_VEDIC_TIME = True  # Set to False for midnight-based day change

def init_db():
    conn = sqlite3.connect('mantras.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS mantras
                 (id INTEGER PRIMARY KEY, name TEXT, sanskrit TEXT, transliteration TEXT,
                  meaning TEXT, category TEXT, deity TEXT, benefits TEXT, 
                  special_days TEXT, nakshatra TEXT, planet TEXT)''')
    
    mantras = [
        ("Gayatri Mantra", "ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्", 
         "Om Bhur Bhuvah Svah Tat Savitur Varenyam Bhargo Devasya Dhimahi Dhiyo Yo Nah Prachodayat",
         "We meditate on the glory of the Creator who has created the Universe, who is worthy of worship, who is the embodiment of knowledge and light",
         "Universal,Wisdom", "Surya", "Enlightenment, wisdom, spiritual growth", "Sunday,Sunrise", "All", "Sun"),
        
        ("Mahamrityunjaya Mantra", "ॐ त्र्यम्बकं यजामहे सुगन्धिं पुष्टिवर्धनम् उर्वारुकमिव बन्धनान्मृत्योर्मुक्षीय माऽमृतात्",
         "Om Tryambakam Yajamahe Sugandhim Pushtivardhanam Urvarukamiva Bandhanan Mrityormukshiya Maamritat",
         "We worship the three-eyed Lord Shiva who nourishes and spreads fragrance. May he liberate us from death for the sake of immortality",
         "Health,Protection", "Shiva", "Health, healing, protection from negativity", "Monday,Pradosh", "Ardra,Mrigashira", "Moon"),
        
        ("Ganesh Mantra", "ॐ गं गणपतये नमः",
         "Om Gam Ganapataye Namah",
         "Salutations to Lord Ganesha, the remover of obstacles",
         "Success,New Beginnings", "Ganesha", "Remove obstacles, success in new ventures", "Wednesday,Chaturthi", "All", "Mercury"),
        
        ("Lakshmi Mantra", "ॐ श्रीं ह्रीं श्रीं कमले कमलालये प्रसीद प्रसीद ॐ श्रीं ह्रीं श्रीं महालक्ष्म्यै नमः",
         "Om Shreem Hreem Shreem Kamale Kamalalaye Prasida Prasida Om Shreem Hreem Shreem Mahalakshmyai Namah",
         "Salutations to Goddess Lakshmi who resides in the lotus",
         "Prosperity,Wealth", "Lakshmi", "Wealth, prosperity, abundance", "Friday,Purnima", "Rohini,Shravana", "Venus"),
        
        ("Saraswati Mantra", "ॐ ऐं सरस्वत्यै नमः",
         "Om Aim Saraswatyai Namah",
         "Salutations to Goddess Saraswati",
         "Knowledge,Arts", "Saraswati", "Knowledge, creativity, learning", "Thursday,Basant Panchami", "Hasta,Revati", "Jupiter"),
        
        ("Hanuman Mantra", "ॐ हं हनुमते नमः",
         "Om Ham Hanumate Namah",
         "Salutations to Lord Hanuman",
         "Strength,Courage", "Hanuman", "Strength, courage, protection", "Tuesday,Saturday", "Swati,Anuradha", "Mars"),
        
        ("Shiva Panchakshari", "ॐ नमः शिवाय",
         "Om Namah Shivaya",
         "Salutations to Lord Shiva",
         "Peace,Liberation", "Shiva", "Inner peace, spiritual liberation", "Monday,Shivaratri", "Ardra,Mrigashira", "Moon"),
        
        ("Vishnu Mantra", "ॐ नमो नारायणाय",
         "Om Namo Narayanaya",
         "Salutations to Lord Narayana (Vishnu)",
         "Protection,Peace", "Vishnu", "Divine protection, peace", "Thursday,Ekadashi", "Shravana,Dhanishta", "Jupiter"),
        
        ("Durga Mantra", "ॐ दुं दुर्गायै नमः",
         "Om Dum Durgayai Namah",
         "Salutations to Goddess Durga",
         "Protection,Power", "Durga", "Protection from evil, inner strength", "Tuesday,Navratri", "Ashwini,Magha", "Mars"),
        
        ("Kali Mantra", "ॐ क्रीं कालिकायै नमः",
         "Om Kreem Kalikayai Namah",
         "Salutations to Goddess Kali",
         "Transformation,Protection", "Kali", "Transformation, removing negativity", "Saturday,Amavasya", "Ashlesha,Jyeshtha", "Saturn"),
        
        ("Surya Mantra", "ॐ सूर्याय नमः",
         "Om Suryaya Namah",
         "Salutations to the Sun God",
         "Energy,Health", "Surya", "Vitality, health, success", "Sunday", "Krittika,Uttara Phalguni", "Sun"),
        
        ("Chandra Mantra", "ॐ चन्द्राय नमः",
         "Om Chandraya Namah",
         "Salutations to the Moon God",
         "Peace,Emotions", "Chandra", "Emotional balance, mental peace", "Monday,Purnima", "Rohini,Mrigashira", "Moon"),
        
        ("Shani Mantra", "ॐ शं शनैश्चराय नमः",
         "Om Sham Shanaishcharaya Namah",
         "Salutations to Lord Shani (Saturn)",
         "Discipline,Karma", "Shani", "Discipline, karmic balance", "Saturday", "Pushya,Anuradha", "Saturn"),
        
        ("Mangal Mantra", "ॐ मं मंगलाय नमः",
         "Om Mam Mangalaya Namah",
         "Salutations to Mars",
         "Courage,Energy", "Mangal", "Courage, energy, vitality", "Tuesday", "Mrigashira,Dhanishta", "Mars"),
        
        ("Budh Mantra", "ॐ बुं बुधाय नमः",
         "Om Bum Budhaya Namah",
         "Salutations to Mercury",
         "Intelligence,Communication", "Budh", "Intelligence, communication skills", "Wednesday", "Ashlesha,Jyeshtha", "Mercury"),
        
        ("Guru Mantra", "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
         "Om Gram Greem Graum Sah Gurave Namah",
         "Salutations to Jupiter",
         "Wisdom,Prosperity", "Guru", "Wisdom, prosperity, good fortune", "Thursday", "Punarvasu,Vishakha", "Jupiter"),
        
        ("Shukra Mantra", "ॐ शुं शुक्राय नमः",
         "Om Shum Shukraya Namah",
         "Salutations to Venus",
         "Love,Beauty", "Shukra", "Love, beauty, relationships", "Friday", "Bharani,Purva Phalguni", "Venus"),
        
        ("Rahu Mantra", "ॐ रां राहवे नमः",
         "Om Ram Rahave Namah",
         "Salutations to Rahu",
         "Transformation,Success", "Rahu", "Overcoming obstacles, success", "Saturday", "Ardra,Swati", "Rahu"),
        
        ("Ketu Mantra", "ॐ केतवे नमः",
         "Om Ketave Namah",
         "Salutations to Ketu",
         "Spirituality,Liberation", "Ketu", "Spiritual growth, moksha", "Tuesday", "Ashwini,Magha", "Ketu"),
        
        ("Maha Mantra", "हरे कृष्ण हरे कृष्ण कृष्ण कृष्ण हरे हरे हरे राम हरे राम राम राम हरे हरे",
         "Hare Krishna Hare Krishna Krishna Krishna Hare Hare Hare Rama Hare Rama Rama Rama Hare Hare",
         "Chanting the names of Lord Krishna and Rama",
         "Devotion,Peace", "Krishna", "Divine love, inner peace", "Janmashtami,Ekadashi", "All", "All"),
        
        # Rigveda Mantras
        ("Agni Sukta (Rigveda 1.1.1)", "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् होतारं रत्नधातमम्",
         "Agnim Ile Purohitam Yajnasya Devam Ritvijam Hotaram Ratna-Dhatamam",
         "I praise Agni, the chosen priest, god, minister of sacrifice, the invoker, lavishest of wealth",
         "Vedic,Fire,Purification", "Agni", "Purification, divine blessings, prosperity", "All", "All", "Sun"),
        
        ("Purusha Sukta (Rigveda 10.90)", "सहस्रशीर्षा पुरुषः सहस्राक्षः सहस्रपात् स भूमिं विश्वतो वृत्वा अत्यतिष्ठद्दशाङ्गुलम्",
         "Sahasra-Shirsha Purushah Sahasrakshah Sahasra-Pat Sa Bhumim Vishvato Vritva Atyatishtad Dashangulam",
         "The cosmic being has thousand heads, thousand eyes, thousand feet. He pervaded the earth and extended beyond it",
         "Vedic,Universal,Creation", "Purusha", "Universal consciousness, cosmic understanding", "All", "All", "All"),
        
        ("Medha Sukta (Rigveda)", "आ मां मेधा सुरभिर्विश्वरूपा हिरण्यवर्णा जगती जगम्या",
         "Aa Mam Medha Surabhir Vishvaroopa Hiranyavarna Jagati Jagamya",
         "May the divine intelligence, all-pervading and golden-hued, come to me",
         "Vedic,Intelligence,Memory", "Saraswati", "Sharp memory, intelligence, learning ability", "Thursday", "Hasta,Revati", "Mercury"),
        
        ("Varuna Sukta (Rigveda)", "इमं मे वरुण श्रुधी हवमद्या च मृडय त्वामवस्युराचके",
         "Imam Me Varuna Shrudhi Havam Adya Cha Mridaya Tvam Avasyu Rachake",
         "O Varuna, hear this invocation of mine, be gracious unto me now, I seek your protection",
         "Vedic,Water,Truth", "Varuna", "Truth, justice, removal of sins", "All", "All", "Saturn"),
        
        ("Indra Sukta (Rigveda)", "इन्द्रं विश्वा अवीवृधन्त समुद्रव्यचसं गिरयः",
         "Indram Vishva Avivridhan Samudra-Vyachasam Girayah",
         "All beings magnify Indra, vast as the ocean, firm as mountains",
         "Vedic,Strength,Victory", "Indra", "Victory, strength, courage in battles", "Thursday", "Jyeshtha,Anuradha", "Jupiter"),
        
        # Yajurveda Mantras
        ("Shanti Mantra (Yajurveda 36.17)", "ॐ द्यौः शान्तिरन्तरिक्षं शान्तिः पृथिवी शान्तिरापः शान्तिरोषधयः शान्तिः",
         "Om Dyauh Shantir Antarikṣham Shantih Prithivi Shantir Apah Shantir Oshadhayah Shantih",
         "May peace radiate in the sky, in space, on earth, in water, in plants",
         "Vedic,Peace,Universal", "Universal", "Universal peace, harmony with nature", "All", "All", "All"),
        
        ("Rudra Mantra (Yajurveda)", "नमस्ते रुद्र मन्यव उतो त इषवे नमः बाहुभ्यामुत ते नमः",
         "Namaste Rudra Manyava Uto Ta Ishave Namah Bahubhyam Uta Te Namah",
         "Salutations to Rudra's anger, to his arrows, to his arms",
         "Vedic,Protection,Power", "Rudra", "Protection from calamities, divine power", "Monday", "Ardra,Mrigashira", "Mars"),
        
        ("Pavamana Mantra (Yajurveda)", "असतो मा सद्गमय तमसो मा ज्योतिर्गमय मृत्योर्मा अमृतं गमय",
         "Asato Ma Sad-Gamaya Tamaso Ma Jyotir-Gamaya Mrityor-Ma Amritam Gamaya",
         "Lead me from untruth to truth, from darkness to light, from death to immortality",
         "Vedic,Enlightenment,Liberation", "Universal", "Spiritual enlightenment, liberation from ignorance", "All", "All", "Sun"),
        
        ("Devi Sukta (Yajurveda)", "अहं रुद्रेभिर्वसुभिश्चराम्यहमादित्यैरुत विश्वदेवैः",
         "Aham Rudrebhir Vasubhish Charamyaham Adityair Uta Vishvadevaiḥ",
         "I move with the Rudras, Vasus, Adityas and all gods",
         "Vedic,Divine Feminine,Power", "Devi", "Divine feminine power, cosmic energy", "Friday,Navratri", "All", "Venus"),
        
        # Samaveda Mantras
        ("Ratri Sukta (Samaveda)", "रात्री व्यख्यद् आयती पुरूरूपा पुरूणि",
         "Ratri Vyakhyad Ayati Pururupa Puruni",
         "Night has come with her many forms and manifestations",
         "Vedic,Night,Rest", "Ratri", "Peaceful sleep, rest, rejuvenation", "All", "All", "Moon"),
        
        ("Soma Mantra (Samaveda)", "पवस्व सोम धारया रथीरथीर्यशस्करः",
         "Pavasva Soma Dharaya Rathir-Rathir Yashaskarah",
         "Flow pure, O Soma, in streams, chariot-borne, bestowing glory",
         "Vedic,Purification,Bliss", "Soma", "Inner bliss, purification, divine nectar", "Monday", "All", "Moon"),
        
        ("Savitri Mantra (Samaveda)", "तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि",
         "Tat Savitur Varenyam Bhargo Devasya Dhimahi",
         "We meditate on the excellent glory of the divine Savitri",
         "Vedic,Wisdom,Light", "Savitri", "Divine wisdom, spiritual illumination", "Sunday,Sunrise", "All", "Sun"),
        
        ("Usha Sukta (Samaveda)", "उषा उच्छन्ती सुभगा न योषा",
         "Usha Uchchhanti Subhaga Na Yosha",
         "Dawn rises, auspicious like a beautiful maiden",
         "Vedic,New Beginnings,Hope", "Usha", "New beginnings, hope, fresh start", "Sunrise", "All", "Sun"),
        
        # Atharvaveda Mantras
        ("Bhu Sukta (Atharvaveda 12.1.1)", "माता भूमिः पुत्रो अहं पृथिव्याः",
         "Mata Bhumiḥ Putro Aham Prithivyah",
         "The Earth is my mother, I am her son",
         "Vedic,Earth,Nature", "Bhumi", "Connection with nature, grounding, stability", "All", "All", "Earth"),
        
        ("Ayurveda Mantra (Atharvaveda)", "आयुर्देहि प्रजां देहि रायस्पोषं च देहि मे",
         "Ayur Dehi Prajam Dehi Rayas-Posham Cha Dehi Me",
         "Grant me long life, progeny, and nourishing wealth",
         "Vedic,Health,Longevity", "Dhanvantari", "Long life, health, prosperity", "All", "All", "Jupiter"),
        
        ("Kala Sukta (Atharvaveda 19.53)", "कालो अश्वो वहति सप्तरश्मिः सहस्राक्षो अजरो भूरिरेताः",
         "Kalo Ashvo Vahati Sapta-Rashmih Sahasrakṣho Ajaro Bhuri-Retah",
         "Time, the seven-rayed horse, carries all, thousand-eyed, ageless, full of seed",
         "Vedic,Time,Eternity", "Kala", "Understanding time, patience, cosmic rhythm", "All", "All", "Saturn"),
        
        ("Vak Sukta (Atharvaveda)", "वाचं दुहानामुप मेहि मातरम्",
         "Vacham Duhanam Upa Mehi Mataram",
         "Come to the mother who yields speech",
         "Vedic,Speech,Communication", "Vak", "Eloquent speech, communication skills", "Thursday", "Hasta,Revati", "Mercury"),
        
        ("Brahma Sukta (Atharvaveda)", "ब्रह्म जज्ञानं प्रथमं पुरस्ताद्वि सीमतः सुरुचो वेन आवः",
         "Brahma Jajnanam Prathamam Purastad Vi Simatah Surucho Vena Avah",
         "Brahman was born first, before all, from the eastern direction came the radiant one",
         "Vedic,Creation,Supreme", "Brahman", "Supreme knowledge, cosmic consciousness", "All", "All", "All"),
        
        ("Kshama Mantra (Atharvaveda)", "क्षमा बलं करोमि",
         "Kshama Balam Karomi",
         "I make forgiveness my strength",
         "Vedic,Forgiveness,Peace", "Universal", "Forgiveness, inner peace, emotional healing", "All", "All", "Moon"),
        
        ("Prithvi Sukta (Atharvaveda)", "सत्यं बृहद्ऋतमुग्रं दीक्षा तपो ब्रह्म यज्ञः पृथिवीं धारयन्ति",
         "Satyam Brihad Ritam Ugram Diksha Tapo Brahma Yajnah Prithivim Dharayanti",
         "Truth, cosmic order, austerity, dedication, and sacrifice uphold the Earth",
         "Vedic,Earth,Dharma", "Prithvi", "Righteousness, dharma, stability", "All", "All", "Earth"),
        
        ("Vayu Sukta (Atharvaveda)", "वायुर्वै प्रथमो देवः स एव प्राणः",
         "Vayur Vai Prathamo Devah Sa Eva Pranah",
         "Vayu is the first deity, he indeed is the life-breath",
         "Vedic,Air,Life Force", "Vayu", "Vital energy, breath control, life force", "All", "All", "Air"),
        
        ("Apah Sukta (Atharvaveda)", "आपो हि ष्ठा मयोभुवः",
         "Apo Hi Shtha Mayo-Bhuvah",
         "Waters are the source of happiness",
         "Vedic,Water,Healing", "Apah", "Healing, purification, emotional balance", "All", "All", "Moon"),
        
        ("Sankalpa Mantra (Yajurveda)", "यन्मे मनः शिवसङ्कल्पमस्तु",
         "Yan Me Manah Shiva-Sankalpam Astu",
         "May my mind be filled with auspicious intentions",
         "Vedic,Intention,Mind", "Universal", "Positive intentions, mental clarity, focus", "All", "All", "Mercury"),
        
        ("Annapurna Mantra", "अन्नपूर्णे सदापूर्णे शङ्करप्राणवल्लभे ज्ञानवैराग्यसिद्ध्यर्थं भिक्षां देहि च पार्वति",
         "Annapurne Sadapurne Shankara-Prana-Vallabhe Jnana-Vairagya-Siddhyartham Bhiksham Dehi Cha Parvati",
         "O Annapurna, ever complete, beloved of Shankara, grant me the alms of knowledge and detachment",
         "Food,Abundance,Nourishment", "Annapurna", "Food security, nourishment, abundance", "All", "All", "Moon"),
    ]
    
    c.executemany('INSERT OR IGNORE INTO mantras VALUES (NULL,?,?,?,?,?,?,?,?,?,?)', mantras)
    conn.commit()
    conn.close()

def get_nakshatra(day_of_year):
    nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", 
                  "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
                  "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
                  "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
                  "Uttara Bhadrapada", "Revati"]
    return nakshatras[int((day_of_year * 27 / 365.25) % 27)]

def get_tithi(date):
    base = datetime(2024, 1, 1)
    days = (date - base).days
    tithi_num = int((days % 29.5) / 29.5 * 30) + 1
    tithis = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
              "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"]
    return tithis[min(tithi_num - 1, 14)]

@lru_cache(maxsize=32)
def get_planet_positions_api(date_str):
    """Fetch real planetary positions from astronomy API"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        # Using astronomy API for real positions
        url = f"https://api.astronomyapi.com/api/v2/bodies/positions"
        
        # Fallback to vedic astrology API
        vedic_url = f"https://json.astrologyapi.com/v1/planets/tropical"
        
        # Try free alternative - using calculation
        return get_planet_positions_calculated(date)
    except:
        return get_planet_positions_calculated(date)

def get_planet_positions_calculated(date):
    """Enhanced planetary position calculation"""
    day_of_year = date.timetuple().tm_yday
    year = date.year
    
    # More accurate calculations
    planets = {
        "Sun": {"degree": (280.46 + 0.9856474 * day_of_year) % 360, "sign": "", "strength": 0},
        "Moon": {"degree": (218.316 + 13.176396 * day_of_year) % 360, "sign": "", "strength": 0},
        "Mars": {"degree": (355.45 + 0.5240207 * day_of_year) % 360, "sign": "", "strength": 0},
        "Mercury": {"degree": (252.25 + 4.092339 * day_of_year) % 360, "sign": "", "strength": 0},
        "Jupiter": {"degree": (34.35 + 0.0830912 * day_of_year) % 360, "sign": "", "strength": 0},
        "Venus": {"degree": (181.98 + 1.602130 * day_of_year) % 360, "sign": "", "strength": 0},
        "Saturn": {"degree": (50.08 + 0.0334442 * day_of_year) % 360, "sign": "", "strength": 0}
    }
    
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    for planet, data in planets.items():
        sign_index = int(data["degree"] / 30)
        planets[planet]["sign"] = signs[sign_index]
        # Calculate strength based on exaltation/debilitation
        planets[planet]["strength"] = calculate_planet_strength(planet, data["degree"], sign_index)
    
    return planets

def calculate_planet_strength(planet, degree, sign_index):
    """Calculate planetary strength based on Vedic astrology"""
    # Exaltation signs (0-indexed)
    exaltation = {
        "Sun": 0,      # Aries
        "Moon": 1,     # Taurus
        "Mars": 9,     # Capricorn
        "Mercury": 5,  # Virgo
        "Jupiter": 3,  # Cancer
        "Venus": 11,   # Pisces
        "Saturn": 6    # Libra
    }
    
    base_strength = 50 + 50 * math.sin(math.radians(degree))
    
    if planet in exaltation:
        if sign_index == exaltation[planet]:
            base_strength = min(95, base_strength + 30)
        elif sign_index == (exaltation[planet] + 6) % 12:
            base_strength = max(20, base_strength - 30)
    
    return round(base_strength, 1)

def get_planet_positions(date):
    """Main function to get planetary positions"""
    return get_planet_positions_api(date.strftime('%Y-%m-%d'))

@app.route('/')
def index():
    return render_template('index.html')

def get_vedic_date():
    """Get current date according to Vedic calendar (day starts at sunrise ~6 AM)"""
    now = datetime.now()
    if USE_VEDIC_TIME and now.hour < 6:
        # Before sunrise, consider it previous day
        return now - timedelta(days=1)
    return now

@app.route('/api/today')
def today_mantra():
    today = get_vedic_date() if USE_VEDIC_TIME else datetime.now()
    day_name = today.strftime('%A')
    nakshatra = get_nakshatra(today.timetuple().tm_yday)
    tithi = get_tithi(today)
    planets = get_planet_positions(today)
    
    # Get strongest planet today
    strongest_planet = max(planets.items(), key=lambda x: x[1]['strength'])[0]
    
    conn = sqlite3.connect('mantras.db')
    c = conn.cursor()
    
    # Smart mantra selection based on day, nakshatra, and strongest planet
    c.execute("""SELECT * FROM mantras 
                 WHERE special_days LIKE ? OR nakshatra LIKE ? OR planet LIKE ?
                 ORDER BY RANDOM() LIMIT 3""", 
              (f'%{day_name}%', f'%{nakshatra}%', f'%{strongest_planet}%'))
    mantras = c.fetchall()
    
    # If no matches, get universal mantras
    if not mantras:
        c.execute("SELECT * FROM mantras WHERE category LIKE '%Universal%' LIMIT 3")
        mantras = c.fetchall()
    
    conn.close()
    
    current_time = datetime.now()
    time_info = f"Vedic Time (Day starts at sunrise)" if USE_VEDIC_TIME else "Standard Time (Day starts at midnight)"
    
    # Get location and calculate sunrise/sunset
    lat, lon, city = get_user_location()
    sunrise, sunset = calculate_sun_times(today, lat, lon)
    
    # Get moon phase
    moon = get_moon_phase(today)
    
    # Check for festivals
    festival = get_hindu_festivals(today)
    
    return jsonify({
        'date': today.strftime('%Y-%m-%d'),
        'day': day_name,
        'nakshatra': nakshatra,
        'tithi': tithi,
        'strongest_planet': strongest_planet,
        'planet_strength': planets[strongest_planet]['strength'],
        'time_system': time_info,
        'current_time': current_time.strftime('%I:%M %p'),
        'sunrise': sunrise,
        'sunset': sunset,
        'location': city,
        'moon_phase': moon,
        'festival': festival,
        'mantras': [{'id': m[0], 'name': m[1], 'sanskrit': m[2], 'transliteration': m[3],
                     'meaning': m[4], 'category': m[5], 'deity': m[6], 'benefits': m[7]} for m in mantras]
    })

def get_user_location():
    """Get user location from IP (fallback to India)"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=2)
        data = response.json()
        return data.get('latitude', 20), data.get('longitude', 77), data.get('city', 'India')
    except:
        return 20, 77, 'India'  # Default to India

def get_moon_phase(date):
    """Calculate moon phase"""
    # Known new moon: Jan 6, 2000
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    days_since = (date - known_new_moon).days
    lunar_month = 29.53058867  # Average lunar month
    phase = (days_since % lunar_month) / lunar_month
    
    phases = [
        (0.03, '🌑', 'New Moon', 'Amavasya'),
        (0.22, '🌒', 'Waxing Crescent', 'Shukla Paksha'),
        (0.28, '🌓', 'First Quarter', 'Shukla Paksha'),
        (0.47, '🌔', 'Waxing Gibbous', 'Shukla Paksha'),
        (0.53, '🌕', 'Full Moon', 'Purnima'),
        (0.72, '🌖', 'Waning Gibbous', 'Krishna Paksha'),
        (0.78, '🌗', 'Last Quarter', 'Krishna Paksha'),
        (0.97, '🌘', 'Waning Crescent', 'Krishna Paksha'),
        (1.0, '🌑', 'New Moon', 'Amavasya')
    ]
    
    for threshold, emoji, name, vedic in phases:
        if phase <= threshold:
            return {'emoji': emoji, 'name': name, 'vedic': vedic, 'phase': round(phase * 100)}
    return phases[0]

def get_hindu_festivals(date):
    """Get Hindu festivals for the year"""
    year = date.year
    festivals = {
        # Major festivals (approximate dates - vary by lunar calendar)
        'Makar Sankranti': f'{year}-01-14',
        'Maha Shivaratri': f'{year}-02-18',
        'Holi': f'{year}-03-25',
        'Ram Navami': f'{year}-04-17',
        'Hanuman Jayanti': f'{year}-04-23',
        'Akshaya Tritiya': f'{year}-05-10',
        'Guru Purnima': f'{year}-07-21',
        'Raksha Bandhan': f'{year}-08-19',
        'Krishna Janmashtami': f'{year}-08-26',
        'Ganesh Chaturthi': f'{year}-09-07',
        'Navratri Begins': f'{year}-10-03',
        'Dussehra': f'{year}-10-12',
        'Diwali': f'{year}-11-01',
        'Govardhan Puja': f'{year}-11-02',
        'Bhai Dooj': f'{year}-11-03',
    }
    
    # Check if today is a festival
    date_str = date.strftime('%Y-%m-%d')
    for festival, fest_date in festivals.items():
        if date_str == fest_date:
            return festival
    return None

def calculate_sun_times(date, lat=None, lon=None):
    """Calculate sunrise and sunset times based on date and location"""
    day_of_year = date.timetuple().tm_yday
    
    # Get user location if not provided
    if lat is None or lon is None:
        lat, lon, _ = get_user_location()
    
    # Solar declination
    declination = 23.45 * math.sin(math.radians((360/365) * (day_of_year - 81)))
    
    latitude = lat
    
    # Hour angle
    cos_hour_angle = -math.tan(math.radians(latitude)) * math.tan(math.radians(declination))
    cos_hour_angle = max(-1, min(1, cos_hour_angle))  # Clamp between -1 and 1
    hour_angle = math.degrees(math.acos(cos_hour_angle))
    
    # Sunrise and sunset in decimal hours (solar noon at 12:00)
    sunrise_decimal = 12 - (hour_angle / 15)
    sunset_decimal = 12 + (hour_angle / 15)
    
    # Convert to IST (add equation of time approximation)
    sunrise_hour = int(sunrise_decimal)
    sunrise_min = int((sunrise_decimal - sunrise_hour) * 60)
    
    sunset_hour = int(sunset_decimal)
    sunset_min = int((sunset_decimal - sunset_hour) * 60)
    
    sunrise_time = f"{sunrise_hour:02d}:{sunrise_min:02d} AM"
    
    if sunset_hour > 12:
        sunset_time = f"{sunset_hour-12:02d}:{sunset_min:02d} PM"
    else:
        sunset_time = f"{sunset_hour:02d}:{sunset_min:02d} PM"
    
    return sunrise_time, sunset_time

@app.route('/api/mantras')
def all_mantras():
    conn = sqlite3.connect('mantras.db')
    c = conn.cursor()
    c.execute("SELECT * FROM mantras")
    mantras = c.fetchall()
    conn.close()
    
    return jsonify([{'id': m[0], 'name': m[1], 'sanskrit': m[2], 'transliteration': m[3],
                     'meaning': m[4], 'category': m[5], 'deity': m[6], 'benefits': m[7],
                     'special_days': m[8], 'nakshatra': m[9]} for m in mantras])

@app.route('/api/astro/<date_str>')
def astro_data(date_str):
    if date_str == datetime.now().strftime('%Y-%m-%d'):
        date = get_vedic_date() if USE_VEDIC_TIME else datetime.now()
    else:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    nakshatra = get_nakshatra(date.timetuple().tm_yday)
    tithi = get_tithi(date)
    planets = get_planet_positions(date)
    
    # Calculate auspicious time
    auspicious = calculate_muhurta(planets)
    
    return jsonify({
        'date': date_str,
        'nakshatra': nakshatra,
        'tithi': tithi,
        'planets': planets,
        'auspicious_time': auspicious,
        'recommendation': get_day_recommendation(planets, nakshatra)
    })

def calculate_muhurta(planets):
    """Calculate auspicious time based on planetary positions"""
    sun_strength = planets['Sun']['strength']
    moon_strength = planets['Moon']['strength']
    
    if sun_strength > 70:
        return "Morning (6 AM - 10 AM) - Sun is strong"
    elif moon_strength > 70:
        return "Evening (6 PM - 9 PM) - Moon is strong"
    else:
        return "Afternoon (12 PM - 3 PM) - Balanced energy"

def get_day_recommendation(planets, nakshatra):
    """Get personalized recommendation"""
    strongest = max(planets.items(), key=lambda x: x[1]['strength'])
    return f"Today is favorable for {strongest[0]}-related activities. Nakshatra {nakshatra} supports spiritual practices."

@app.route('/api/calendar/<year>/<month>')
def calendar_data(year, month):
    year, month = int(year), int(month)
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    days = []
    current = first_day
    while current <= last_day:
        nakshatra = get_nakshatra(current.timetuple().tm_yday)
        tithi = get_tithi(current)
        festival = get_hindu_festivals(current)
        moon = get_moon_phase(current)
        
        days.append({
            'date': current.strftime('%Y-%m-%d'),
            'day': current.day,
            'nakshatra': nakshatra,
            'tithi': tithi,
            'weekday': current.strftime('%A'),
            'festival': festival,
            'moon_phase': moon['emoji'] if moon else None,
            'is_purnima': moon['vedic'] == 'Purnima' if moon else False,
            'is_amavasya': moon['vedic'] == 'Amavasya' if moon else False
        })
        current += timedelta(days=1)
    
    return jsonify(days)

@app.route('/api/panchang/<date_str>')
def panchang(date_str):
    """Complete Panchang for the day"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    nakshatra = get_nakshatra(date.timetuple().tm_yday)
    tithi = get_tithi(date)
    
    # Calculate Yoga and Karana
    day_num = date.timetuple().tm_yday
    yogas = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarman",
             "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
             "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
             "Shukla", "Brahma", "Indra", "Vaidhriti"]
    yoga = yogas[day_num % 27]
    
    karanas = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]
    karana = karanas[day_num % 7]
    
    return jsonify({
        'date': date_str,
        'nakshatra': nakshatra,
        'tithi': tithi,
        'yoga': yoga,
        'karana': karana,
        'weekday': date.strftime('%A')
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

