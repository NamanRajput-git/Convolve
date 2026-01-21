"""
Seed verified medical knowledge into Qdrant
Run this once to populate the medical knowledge base
"""

from embeddings import embedding_encoder
from qdrant_manager import qdrant_client
import config
from loguru import logger


# WHO-verified maternal health guidance (Enhanced)
MEDICAL_KNOWLEDGE = [
    # --- DANGER SIGNS ---
    {
        "content": "Severe bleeding during pregnancy (APH) or after delivery (PPH) is a medical emergency. Go to hospital immediately.",
        "content_hi": "गर्भावस्था या प्रसव के बाद ज्यादा खून बहना खतरनाक है। तुरंत अस्पताल जाएं।",
        "topic": "danger_signs",
        "source": "WHO Maternal Health Guidelines",
        "confidence": 1.0
    },
    {
        "content": "Severe headache, blurred vision, or swelling of face/hands indicates preeclampsia (high BP). Seek immediate medical care.",
        "content_hi": "तेज सिरदर्द, धुंधला दिखना, या चेहरे/हाथों पर सूजन हाई-बीपी (प्रीक्लेम्पसिया) का संकेत है। तुरंत डॉक्टर को दिखाएं।",
        "topic": "danger_signs",
        "source": "WHO/NHM Guidelines",
        "confidence": 0.99
    },
    {
        "content": "Convulsions or fits during pregnancy are life-threatening (Eclampsia). Call for help and transport to facility immediately.",
        "content_hi": "गर्भावस्था में दौरे पड़ना जानलेवा हो सकता है। तुरंत अस्पताल ले जाएं।",
        "topic": "danger_signs",
        "source": "WHO",
        "confidence": 1.0
    },
    {
        "content": "High fever (>38°C) with foul discharge or abdominal pain indicates sepsis/infection. Needs antibiotics immediately.",
        "content_hi": "तेज बुखार, बदबूदार स्राव या पेट दर्द संक्रमण का संकेत है। तुरंत इलाज कराएं।",
        "topic": "danger_signs",
        "source": "NHM Dakshata Guidelines",
        "confidence": 0.95
    },
    {
        "content": "Reduced fetal movements: If baby moves less than 10 times in 12 hours, consult doctor immediately.",
        "content_hi": "अगर शिशु 12 घंटे में 10 बार से कम हलचल करे, तो तुरंत डॉक्टर से मिलें।",
        "topic": "danger_signs",
        "source": "ACOG/WHO",
        "confidence": 0.95
    },

    # --- ANEMIA & NUTRITION ---
    {
        "content": "Severe Anemia (Hb < 7 g/dL): Symptoms include extreme fatigue, breathlessness at rest, pale palms. Requires immediate treatment.",
        "content_hi": "गंभीर एनीमिया: बहुत थकान, सांस फूलना, पीली हथेली। तुरंत इलाज जरूरी है।",
        "topic": "anemia",
        "source": "Anemia Mukt Bharat",
        "confidence": 0.98
    },
    {
        "content": "Take 1 IFA tablet (Iron-Folic Acid) daily from 4th month of pregnancy till 6 months after delivery. Prevents anemia.",
        "content_hi": "गर्भावस्था के चौथे महीने से रोज एक IFA (आयरन) की गोली लें। यह खून की कमी रोकती है।",
        "topic": "nutrition",
        "source": "Anemia Mukt Bharat",
        "confidence": 1.0
    },
    {
        "content": "Calcium Supplementation: Take 2 tablets (500mg each) daily after meals from 14 weeks. Do not take with Iron tablet.",
        "content_hi": "कैल्शियम की 2 गोलियां रोज खाने के बाद लें। आयरन की गोली के साथ न लें।",
        "topic": "nutrition",
        "source": "Maternal Nutrition Guidelines India",
        "confidence": 0.95
    },
    {
        "content": "Pregnancy Diet: Needs extra food (+350 calories). Eat pulses, milk, eggs, green leafy vegetables, and nuts. Tiranga Bhojan (Tri-color food) is best.",
        "content_hi": "गर्भावस्था में ज्यादा खाना जरूरी है। दाल, दूध, अंडा, हरी सब्जियां और सूखे मेवे खाएं।",
        "topic": "nutrition",
        "source": "Poshan Abhiyaan",
        "confidence": 0.95
    },

    # --- ANTENATAL CARE ---
    {
        "content": "Minimum 4 ANC Checkups are mandatory: 1st (within 12 weeks), 2nd (14-26 weeks), 3rd (28-34 weeks), 4th (36 weeks-term).",
        "content_hi": "गर्भावस्था में कम से कम 4 जांच जरूरी हैं: पहली 3 महीने में, दूसरी 5-6 महीने में, तीसरी 7-8 महीने में, चौथी 9 महीने में।",
        "topic": "antenatal_care",
        "source": "Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA)",
        "confidence": 1.0
    },
    {
        "content": "Get 2 doses of Tetanus Toxoid (TT) vaccine during pregnancy to protect mother and baby from Tetanus.",
        "content_hi": "गर्भावस्था में टिटनेस (TT) के 2 टीके जरूर लगवाएं।",
        "topic": "antenatal_care",
        "source": "Universal Immunization Programme",
        "confidence": 1.0
    },

    # --- NEWBORN CARE ---
    {
        "content": "Essential Newborn Care: Dry baby immediately, Skin-to-skin contact, Delayed cord clamping, Breastfeeding within 1 hour. Do NOT bathe baby for 24 hours.",
        "content_hi": "शिशु की देखभाल: तुरंत पोंछें, माँ से चिपकाकर रखें, 1 घंटे में स्तनपान कराएं। 24 घंटे तक न नहलाएं।",
        "topic": "newborn_care",
        "source": "NSSK Guidelines",
        "confidence": 0.98
    },
    {
        "content": "Newborn Danger Signs: Not feeding, convulsions, fast breathing (>60/min), chest indrawing, fever or cold body. Refer to SNCU immediately.",
        "content_hi": "नवजात खतरे के संकेत: दूध न पीना, दौरे, तेज सांस, बुखार या शरीर ठंडा पड़ना। तुरंत अस्पताल ले जाएं।",
        "topic": "newborn_care",
        "source": "HBNC Guidelines",
        "confidence": 0.98
    },
    {
        "content": "Exclusive Breastfeeding: Give ONLY breastmilk for first 6 months. No water, honey, or ghutti. Colostrum (first yellow milk) is mandatory.",
        "content_hi": "पहले 6 महीने सिर्फ माँ का दूध पिलाएं। पानी, शहद या घुट्टी न दें। पहला पीला दूध जरूर पिलाएं।",
        "topic": "breastfeeding",
        "source": "MAA Programme",
        "confidence": 1.0
    },

    # --- GOVT SCHEMES ---
    {
        "content": "Janani Suraksha Yojana (JSY): Cash assistance for institutional delivery (Rs 1400 in rural areas). ASHA helps you.",
        "content_hi": "जननी सुरक्षा योजना (JSY): अस्पताल में प्रसव के लिए नकद सहायता (ग्रामीण में 1400 रुपये)। आशा दीदी मदद करेगी।",
        "topic": "schemes",
        "source": "NHM Guidelines",
        "confidence": 0.95
    },
    {
        "content": "JSSK Scheme: Free delivery, free drugs, free diagnostics, free diet, and free transport (home-to-hospital-to-home).",
        "content_hi": "JSSK योजना: मुफ्त प्रसव, मुफ्त दवा, मुफ्त जांच, मुफ्त खाना, और मुफ्त एम्बुलेंस सुविधा।",
        "topic": "schemes",
        "source": "NHM Guidelines",
        "confidence": 0.96
    },
    {
        "content": "PMMVY: Rs 5000 cash incentive for first child in 3 installments for nutrition support.",
        "content_hi": "PMMVY: पहले बच्चे के लिए 5000 रुपये की नकद सहायता (3 किश्तों में)।",
        "topic": "schemes",
        "source": "WCD Ministry",
        "confidence": 0.95
    }
]

# Verified Nutrition Data
NUTRITION_PATTERNS = [
    {
        "food_item": "Spinach (Palak)",
        "local_name": "पालक (Palak)",
        "content": "Spinach is rich in Iron and Folic Acid. Eat with lemon (Vitamin C) for better absorption.",
        "description": "Excellent for preventing anemia"
    },
    {
        "food_item": "Jaggery (Gur)",
        "local_name": "गुड़ (Gur)",
        "content": "Jaggery helps boost hemoglobin. Replace sugar with jaggery.",
        "description": "Natural iron source"
    },
    {
        "food_item": "Lentils/Pulses (Dal)",
        "local_name": "दाल (Dal)",
        "content": "Dal provides Protein for baby's growth. Eat yellow and black dal daily.",
        "description": "Protein source"
    },
    {
        "food_item": "Milk & Curd",
        "local_name": "दूध-दही (Milk/Curd)",
        "content": "Milk products provide Calcium key for baby's bones. Drink 2 glasses daily.",
        "description": "Calcium source"
    },
    {
        "food_item": "Egg",
        "local_name": "अंडा (Egg)",
        "content": "Eggs are a complete protein source. Eat boiled egg daily if non-veg.",
        "description": "Complete nutrition"
    },
    {
        "food_item": "Drumstick Leaves (Moringa)",
        "local_name": "सहजन की पत्तियां (Moringa)",
        "content": "Moringa leaves are a superfood with very high Iron and Calcium.",
        "description": "Superfood for anemia"
    }
]


def seed_medical_knowledge():
    """Seed verified medical knowledge"""
    logger.info("Seeding medical knowledge...")
    
    points = []
    for i, item in enumerate(MEDICAL_KNOWLEDGE):
        # Combine English and Hindi for better retrieval
        combined_text = f"{item['content']} {item['content_hi']}"
        
        # Generate embedding
        vector = embedding_encoder.encode(combined_text)
        
        # Create point
        point = {
            "id": i + 1,
            "vector": vector,
            "payload": {
                "content": item["content"],
                "content_hi": item["content_hi"],
                "topic": item["topic"],
                "source": item["source"],
                "confidence": item["confidence"]
            }
        }
        points.append(point)
    
    # Upsert to Qdrant
    qdrant_client.client.upsert(
        collection_name=config.COLLECTION_MEDICAL_KNOWLEDGE,
        points=points
    )
    
    logger.info(f"✅ Seeded {len(points)} medical knowledge items")


def seed_nutrition_patterns():
    """Seed nutrition pattern data"""
    logger.info("Seeding nutrition patterns...")
    
    points = []
    for i, item in enumerate(NUTRITION_PATTERNS):
        # Create searchable text
        text = f"{item['food_item']} {item['local_name']} {item['content']} {item['description']}"
        
        # Generate embedding
        vector = embedding_encoder.encode(text)
        
        # Create point
        point = {
            "id": i + 1,
            "vector": vector,
            "payload": {
                "food_item": item['food_item'],
                "local_name": item['local_name'],
                "description": item['description'],
                "content": item['content']
            }
        }
        points.append(point)
    
    # Upsert to Qdrant
    qdrant_client.client.upsert(
        collection_name=config.COLLECTION_NUTRITION_PATTERNS,
        points=points
    )
    
    logger.info(f"✅ Seeded {len(points)} nutrition patterns")


if __name__ == "__main__":
    logger.info("Starting knowledge base seeding...")
    seed_medical_knowledge()
    seed_nutrition_patterns()
    logger.info("✅ Knowledge base seeding complete!")
