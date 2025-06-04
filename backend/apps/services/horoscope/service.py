import json
import logging
import os
import random
import re
from datetime import date
from typing import Tuple, Dict, Any
from openai import OpenAI

from ...core.logger import setup_logging
# logger = setup_logging("Horoscope")

from ...config import get_settings
settings = get_settings()

class HoroscopeService:
    def __init__(self):
        # self.api_key = settings.deepseek_api_key
        self.api_key = settings.openai_api_key
        # self.client = OpenAI(
        #     api_key=self.api_key,
        #     base_url="https://api.deepseek.com"
        # )
        self.client = OpenAI(
            api_key=self.api_key
        )
        self.zodiac_names = {
            "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                   "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "zh": ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
                   "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"]
        }
        self.logger = setup_logging("Horoscope")

    def get_zodiac_sign(self, birthdate: date, language: str = "en") -> Tuple[str, str]:
        """Determine zodiac sign based on birthdate."""
        self.logger.info(f"Getting information for user with birthdate: {birthdate}")
        month = birthdate.month
        day = birthdate.day
        index = -1

        try:
            index = self._get_index(month, day)
        except Exception as e:
            self.logger.error(f"An error {str(e)} occurred when trying to get index for birthdate: {str(birthdate)}")

        english_name = self.zodiac_names["en"][index]
        localized_name = self.zodiac_names[language][index] if language in self.zodiac_names else english_name

        return english_name, localized_name

    async def get_daily_horoscope(self, zodiac_sign: str, gender: str, language: str = "en") -> Dict[str, Any]:
        """Generate a daily horoscope using DeepSeek API."""
        try:
            # Create prompt for DeepSeek based on language
            prompt = self._prompt_generator(language, zodiac_sign, gender)

            if self.api_key:
                try:
                    input_text = prompt
                    response = self.client.responses.create(
                        model="gpt-3.5-turbo",
                        input=input_text,
                    )

                    if hasattr(response, 'output') and len(response.output) > 0:
                        # The output format referred to official doc:
                        # https://platform.openai.com/docs/api-reference/responses/create
                        horoscope_text = response.output[0].content[0].text

                        # Process potential Markdown output from Deepseek
                        if "```json" in horoscope_text:
                            # Extract JSON
                            json_start = horoscope_text.find('{')
                            json_end = horoscope_text.rfind('}') + 1
                            if 0 <= json_start < json_end:
                                horoscope_text = horoscope_text[json_start:json_end]

                        try:
                            horoscope_data = json.loads(horoscope_text)
                            # logging.info(f"Got horoscope data: {horoscope_data}")
                            horoscope_data["zodiac_sign"] = zodiac_sign

                            if language == "zh" and zodiac_sign in self.zodiac_names["zh"]:
                                horoscope_data["zodiac_sign_chinese"] = zodiac_sign
                                if zodiac_sign in self.zodiac_names["zh"]:
                                    index = self.zodiac_names["zh"].index(zodiac_sign)
                                    horoscope_data["zodiac_sign"] = self.zodiac_names["en"][index]
                            elif zodiac_sign in self.zodiac_names["en"]:
                                index = self.zodiac_names["en"].index(zodiac_sign)
                                horoscope_data["zodiac_sign_chinese"] = self.zodiac_names["zh"][index]

                            return horoscope_data
                        except json.JSONDecodeError as json_error:
                            self.logger.error(f"Failed to parse JSON content: {str(json_error)}")
                            try:
                                cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', horoscope_text)
                                cleaned_text = cleaned_text.replace('\n', ' ').replace('\\', '\\\\')
                                horoscope_data = json.loads(cleaned_text)

                                horoscope_data["zodiac_sign"] = zodiac_sign
                                if language == "zh" and zodiac_sign in self.zodiac_names["zh"]:
                                    pass
                                elif zodiac_sign in self.zodiac_names["en"]:
                                    index = self.zodiac_names["en"].index(zodiac_sign)
                                    horoscope_data["zodiac_sign_chinese"] = self.zodiac_names["zh"][index]

                                return horoscope_data
                            except:
                                return self._generate_fallback_horoscope(zodiac_sign, language)
                    else:
                        self.logger.error("Response does not have choice field as expected")
                        return self._generate_fallback_horoscope(zodiac_sign, language)

                except Exception as api_error:
                    self.logger.error(f"Error happened when trying to make API call: {str(api_error)}")
                    import traceback
                    traceback.print_exc()
                    return self._generate_fallback_horoscope(zodiac_sign, language)
            else:
                self.logger.error("No API Key provided")
                return self._generate_fallback_horoscope(zodiac_sign, language)

        except Exception as e:
            self.logger.error(f"Error occurred before making API call: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_horoscope(zodiac_sign, language)

    def _generate_fallback_horoscope(self, zodiac_sign: str, language: str = "en") -> Dict[str, Any]:
        """Generate a fallback horoscope if the API call fails."""
        lucky_number = random.randint(1, 100)

        # Get English name and localized name
        if zodiac_sign in self.zodiac_names["en"]:
            english_name = zodiac_sign
            index = self.zodiac_names["en"].index(english_name)
            localized_name = self.zodiac_names[language][index] if language in self.zodiac_names else english_name
        elif language == "zh" and zodiac_sign in self.zodiac_names["zh"]:
            localized_name = zodiac_sign
            index = self.zodiac_names["zh"].index(localized_name)
            english_name = self.zodiac_names["en"][index]
        else:
            # Default: Aris
            english_name = "Aries"
            localized_name = self.zodiac_names[language][0] if language in self.zodiac_names else english_name

        # Choose a random compatible zodiac
        compatible_sign_index = random.choice([i for i in range(12) if self.zodiac_names["en"][i] != english_name])
        compatible_sign_en = self.zodiac_names["en"][compatible_sign_index]
        compatible_sign = self.zodiac_names[language][compatible_sign_index] if language == "zh" else compatible_sign_en

        moods = {
            "en": ["Happy", "Reflective", "Energetic", "Calm", "Inspired", "Ambitious", "Peaceful"],
            "zh": ["开心", "沉思", "精力充沛", "平静", "受启发", "雄心勃勃", "安宁"]
        }
        mood = random.choice(moods.get(language, moods["en"]))

        # Get horoscope templates for the specified language
        horoscopes = self._get_horoscope_templates(language)

        # Choose appropriate horoscope text
        if language == "zh":
            horoscope_text = horoscopes.get(localized_name,
                                            "今天带来新的机遇和挑战。相信你的直觉，对意外的可能性保持开放的态度。")
        else:
            horoscope_text = horoscopes.get(english_name,
                                            "Today brings new opportunities and challenges. Trust your instincts and remain open to unexpected possibilities.")

        return {
                "zodiac_sign": english_name,
                "zodiac_sign_chinese": localized_name,
                "daily_horoscope": horoscope_text,
                "lucky_number": lucky_number,
                "compatibility": compatible_sign,
                "mood": mood
            }

    @staticmethod
    def _get_index(month, day) -> int:
        if (month == 3 and day >= 21) or (month == 4 and day <= 19):
            index = 0  # Aries
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            index = 1  # Taurus
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            index = 2  # Gemini
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            index = 3  # Cancer
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            index = 4  # Leo
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            index = 5  # Virgo
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            index = 6  # Libra
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            index = 7  # Scorpio
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            index = 8  # Sagittarius
        elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
            index = 9  # Capricorn
        elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
            index = 10  # Aquarius
        else:
            index = 11  # Pisces
        return index

    @staticmethod
    def _prompt_generator(language: str, zodiac_sign: str, gender: str):
        if language == "zh":
            prompt = f"""
            为一位{gender}的{zodiac_sign}生成今日运势预测。
            包括他们今天的整体运势，一个1到100之间的幸运数字，
            今天最相配的星座，以及一个描述心情的词。
            请使用以下JSON格式回复：
            {{
                "daily_horoscope": "详细的运势预测文本（150-200字）",
                "lucky_number": 幸运数字（整数）,
                "compatibility": "相配的星座",
                "mood": "心情描述"
            }}
            使运势预测详细、有洞察力，积极但也要实际。
            请直接返回JSON，不要包含任何额外的标记或文本。
            """
        else:
            prompt = f"""
            Generate a daily horoscope for a {gender} who is a {zodiac_sign}.
            Include their overall forecast for today, a lucky number between 1 and 100,
            a compatible zodiac sign for today, and a mood descriptor.
            Format the response as JSON with the following structure:
            {{
                "daily_horoscope": "detailed horoscope text (150-200 words)",
                "lucky_number": lucky_number_as_integer,
                "compatibility": "compatible zodiac sign",
                "mood": "mood descriptor"
            }}
            Make the horoscope detailed, insightful, and positive but realistic.
            Return ONLY the JSON without any markdown formatting or additional text.
            """

        return prompt

    @staticmethod
    def _get_horoscope_templates(language: str = "en"):
        """Return horoscope template with given language"""
        if language == "zh":
            return {
                "白羊座": "今天带来了新开始的机会。你天生的领导能力将闪耀光芒，帮助你自信地应对挑战。对于你内心珍视的项目，主动出击吧。",
                "金牛座": "今天稳定和舒适感成为重点。专注于自我照顾和建立有益健康的日常习惯。财务问题可能需要关注，但你的实际做法会让你应对自如。",
                "双子座": "今天沟通顺畅。你的好奇心引领你进行有趣的对话和建立新的联系。平衡社交活动和个人项目的时间来保持精力充沛。",
                "巨蟹座": "今天情感智慧指引着你。在做决定时信任你的直觉。家庭和家人事务带来喜悦和舒适，为你敏感的心灵创造一个安全港。",
                "狮子座": "今天你的创造能量达到顶峰。大胆表达自己并与他人分享你的才华。认可可能来自意想不到的地方，肯定你独特的天赋。",
                "处女座": "今天细节至关重要，你的分析思维能够发现重要的模式。组织带来内心平静，让你能够轻松应对复杂问题。",
                "天秤座": "今天人际关系中的和谐被突显。你的外交技巧帮助解决冲突并创造平衡。美的享受带来喜悦，所以在一天中留出时间感受美好。",
                "天蝎座": "今天通过深刻的情感理解可能实现转变。信任你对他人动机的直觉。你的热情和决心帮助克服障碍。",
                "射手座": "今天冒险在召唤，无论是身体上还是智力上的。通过学习或旅行扩展你的视野。你的乐观精神激励周围的人思考更大的可能性。",
                "摩羯座": "今天通过有纪律的努力实现目标进展。你的实用方法有效地解决问题。过去工作的认可增强了你对自己道路的信心。",
                "水瓶座": "今天创新是你的强项。当你跳出常规思考时，旧问题的独特解决方案就会浮现。与志同道合的人联系以获取灵感。",
                "双鱼座": "今天直觉和创造力流动。艺术活动特别有回报。你富有同情心的本性帮助他人，但记得保持健康的界限。"
            }
        else:
            return {
                "Aries": "Today brings opportunities for new beginnings. Your natural leadership abilities shine through, helping you navigate challenges with confidence. Take initiative on projects close to your heart.",
                "Taurus": "Stability and comfort are highlighted today. Focus on self-care and establishing routines that nurture your wellbeing. Financial matters may require attention, but your practical approach serves you well.",
                "Gemini": "Communication flows easily today. Your curiosity leads to interesting conversations and connections. Balance social activities with time for personal projects to maintain energy.",
                "Cancer": "Emotional intelligence guides you today. Trust your intuition when making decisions. Home and family matters bring joy and comfort, creating a sanctuary for your sensitive spirit.",
                "Leo": "Your creative energy is at a peak today. Express yourself boldly and share your talents with others. Recognition may come from unexpected sources, affirming your unique gifts.",
                "Virgo": "Details matter today, and your analytical mind spots important patterns. Organization brings peace of mind, allowing you to tackle complex problems with ease.",
                "Libra": "Harmony in relationships is highlighted today. Your diplomatic skills help resolve conflicts and create balance. Aesthetic pleasures bring joy, so make time for beauty in your day.",
                "Scorpio": "Transformation is possible today through deep emotional understanding. Trust your instincts about others' motivations. Your passion and determination help overcome obstacles.",
                "Sagittarius": "Adventure calls today, whether physical or intellectual. Expand your horizons through learning or travel. Your optimism inspires those around you to think bigger.",
                "Capricorn": "Progress toward goals comes through disciplined effort today. Your practical approach solves problems efficiently. Recognition for past work boosts confidence in your path.",
                "Aquarius": "Innovation is your strength today. Unique solutions to old problems emerge when you think outside conventional boundaries. Connect with like-minded individuals for inspiration.",
                "Pisces": "Intuition and creativity flow today. Artistic endeavors are especially rewarding. Your compassionate nature helps others, but remember to maintain healthy boundaries."
            }