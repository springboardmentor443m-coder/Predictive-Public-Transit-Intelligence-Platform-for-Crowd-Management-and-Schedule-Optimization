import sys
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.models.station import Station
from app.models.ridership import RidershipLog
from app.models.train_status import TrainStatus
from app.models.alert import Alert

# High-fidelity authentic Seoul Metro Stations dataset covering Lines 1-9 & transfer hubs
SEOUL_STATIONS_DEFAULT = [
    # Line 1
    {"station_code": "150", "name_en": "Seoul Station", "name_kr": "서울역", "line": "Line 1", "latitude": 37.554648, "longitude": 126.972559, "district": "Jung-gu"},
    {"station_code": "151", "name_en": "City Hall", "name_kr": "시청", "line": "Line 1", "latitude": 37.564718, "longitude": 126.977108, "district": "Jung-gu"},
    {"station_code": "152", "name_en": "Jonggak", "name_kr": "종각", "line": "Line 1", "latitude": 37.570161, "longitude": 126.982923, "district": "Jongno-gu"},
    {"station_code": "153", "name_en": "Jongno 3-ga", "name_kr": "종로3가", "line": "Line 1", "latitude": 37.571607, "longitude": 126.991806, "district": "Jongno-gu"},
    {"station_code": "154", "name_en": "Jongno 5-ga", "name_kr": "종로5가", "line": "Line 1", "latitude": 37.570926, "longitude": 127.001849, "district": "Jongno-gu"},
    {"station_code": "155", "name_en": "Dongdaemun", "name_kr": "동대문", "line": "Line 1", "latitude": 37.571420, "longitude": 127.009745, "district": "Jongno-gu"},
    {"station_code": "156", "name_en": "Sinseol-dong", "name_kr": "신설동", "line": "Line 1", "latitude": 37.575297, "longitude": 127.025087, "district": "Dongdaemun-gu"},
    {"station_code": "157", "name_en": "Jegi-dong", "name_kr": "제기동", "line": "Line 1", "latitude": 37.577979, "longitude": 127.034821, "district": "Dongdaemun-gu"},
    {"station_code": "158", "name_en": "Cheongnyangni", "name_kr": "청량리", "line": "Line 1", "latitude": 37.580178, "longitude": 127.046835, "district": "Dongdaemun-gu"},
    {"station_code": "159", "name_en": "Dongmyo", "name_kr": "동묘앞", "line": "Line 1", "latitude": 37.572627, "longitude": 127.016429, "district": "Jongno-gu"},
    {"station_code": "1001", "name_en": "Yongsan", "name_kr": "용산", "line": "Line 1", "latitude": 37.529883, "longitude": 126.964775, "district": "Yongsan-gu"},
    {"station_code": "1002", "name_en": "Noryangjin", "name_kr": "노량진", "line": "Line 1", "latitude": 37.513490, "longitude": 126.940000, "district": "Dongjak-gu"},
    {"station_code": "1003", "name_en": "Yeongdeungpo", "name_kr": "영등포", "line": "Line 1", "latitude": 37.515572, "longitude": 126.907605, "district": "Yeongdeungpo-gu"},
    {"station_code": "1004", "name_en": "Sindorim", "name_kr": "신도림", "line": "Line 1", "latitude": 37.508815, "longitude": 126.891222, "district": "Guro-gu"},
    {"station_code": "1005", "name_en": "Guro", "name_kr": "구로", "line": "Line 1", "latitude": 37.503039, "longitude": 126.881969, "district": "Guro-gu"},

    # Line 2 (Circle Line & Key Hubs)
    {"station_code": "201", "name_en": "City Hall (L2)", "name_kr": "시청 (2호선)", "line": "Line 2", "latitude": 37.564718, "longitude": 126.977108, "district": "Jung-gu"},
    {"station_code": "202", "name_en": "Euljiro 1-ga", "name_kr": "을지로입구", "line": "Line 2", "latitude": 37.566014, "longitude": 126.982618, "district": "Jung-gu"},
    {"station_code": "203", "name_en": "Euljiro 3-ga", "name_kr": "을지로3가", "line": "Line 2", "latitude": 37.566295, "longitude": 126.991983, "district": "Jung-gu"},
    {"station_code": "204", "name_en": "Euljiro 4-ga", "name_kr": "을지로4가", "line": "Line 2", "latitude": 37.566941, "longitude": 126.998079, "district": "Jung-gu"},
    {"station_code": "205", "name_en": "Dongdaemun History & Culture Park", "name_kr": "동대문역사문화공원", "line": "Line 2", "latitude": 37.565138, "longitude": 127.007896, "district": "Jung-gu"},
    {"station_code": "206", "name_en": "Sindang", "name_kr": "신당", "line": "Line 2", "latitude": 37.565715, "longitude": 127.019445, "district": "Jung-gu"},
    {"station_code": "207", "name_en": "Sangwangsimni", "name_kr": "상왕십리", "line": "Line 2", "latitude": 37.564352, "longitude": 127.029354, "district": "Seongdong-gu"},
    {"station_code": "208", "name_en": "Wangsimni", "name_kr": "왕십리", "line": "Line 2", "latitude": 37.561533, "longitude": 127.037732, "district": "Seongdong-gu"},
    {"station_code": "209", "name_en": "Hanyang Univ.", "name_kr": "한양대", "line": "Line 2", "latitude": 37.555273, "longitude": 127.043691, "district": "Seongdong-gu"},
    {"station_code": "210", "name_en": "Ttukseom", "name_kr": "뚝섬", "line": "Line 2", "latitude": 37.547184, "longitude": 127.047377, "district": "Seongdong-gu"},
    {"station_code": "211", "name_en": "Seongsu", "name_kr": "성수", "line": "Line 2", "latitude": 37.544583, "longitude": 127.055961, "district": "Seongdong-gu"},
    {"station_code": "212", "name_en": "Konkuk Univ.", "name_kr": "건대입구", "line": "Line 2", "latitude": 37.540693, "longitude": 127.069232, "district": "Gwangjin-gu"},
    {"station_code": "213", "name_en": "Guui", "name_kr": "구의", "line": "Line 2", "latitude": 37.537077, "longitude": 127.085916, "district": "Gwangjin-gu"},
    {"station_code": "214", "name_en": "Gangbyeon", "name_kr": "강변", "line": "Line 2", "latitude": 37.535095, "longitude": 127.094686, "district": "Gwangjin-gu"},
    {"station_code": "215", "name_en": "Jamsillaru", "name_kr": "잠실나루", "line": "Line 2", "latitude": 37.520731, "longitude": 127.103790, "district": "Songpa-gu"},
    {"station_code": "216", "name_en": "Jamsil", "name_kr": "잠실", "line": "Line 2", "latitude": 37.513262, "longitude": 127.100133, "district": "Songpa-gu"},
    {"station_code": "217", "name_en": "Jamsilsaenae", "name_kr": "잠실새내", "line": "Line 2", "latitude": 37.511687, "longitude": 127.086162, "district": "Songpa-gu"},
    {"station_code": "218", "name_en": "Sports Complex", "name_kr": "종합운동장", "line": "Line 2", "latitude": 37.511002, "longitude": 127.073620, "district": "Songpa-gu"},
    {"station_code": "219", "name_en": "Samseong (COEX)", "name_kr": "삼성", "line": "Line 2", "latitude": 37.508844, "longitude": 127.063160, "district": "Gangnam-gu"},
    {"station_code": "220", "name_en": "Seolleung", "name_kr": "선릉", "line": "Line 2", "latitude": 37.504286, "longitude": 127.048203, "district": "Gangnam-gu"},
    {"station_code": "221", "name_en": "Yeoksam", "name_kr": "역삼", "line": "Line 2", "latitude": 37.500622, "longitude": 127.036456, "district": "Gangnam-gu"},
    {"station_code": "222", "name_en": "Gangnam", "name_kr": "강남", "line": "Line 2", "latitude": 37.497952, "longitude": 127.027619, "district": "Gangnam-gu"},
    {"station_code": "223", "name_en": "Seoul Nat'l Univ. of Education", "name_kr": "교대", "line": "Line 2", "latitude": 37.493415, "longitude": 127.014080, "district": "Seocho-gu"},
    {"station_code": "224", "name_en": "Seocho", "name_kr": "서초", "line": "Line 2", "latitude": 37.491897, "longitude": 127.007917, "district": "Seocho-gu"},
    {"station_code": "225", "name_en": "Bangbae", "name_kr": "방배", "line": "Line 2", "latitude": 37.481426, "longitude": 126.997596, "district": "Seocho-gu"},
    {"station_code": "226", "name_en": "Sadang", "name_kr": "사당", "line": "Line 2", "latitude": 37.476530, "longitude": 126.981685, "district": "Dongjak-gu"},
    {"station_code": "227", "name_en": "Nakseongdae", "name_kr": "낙성대", "line": "Line 2", "latitude": 37.476929, "longitude": 126.963690, "district": "Gwanak-gu"},
    {"station_code": "228", "name_en": "Seoul Nat'l Univ.", "name_kr": "서울대입구", "line": "Line 2", "latitude": 37.481247, "longitude": 126.952739, "district": "Gwanak-gu"},
    {"station_code": "229", "name_en": "Bongcheon", "name_kr": "봉천", "line": "Line 2", "latitude": 37.482364, "longitude": 126.941892, "district": "Gwanak-gu"},
    {"station_code": "230", "name_en": "Sillim", "name_kr": "신림", "line": "Line 2", "latitude": 37.484201, "longitude": 126.929715, "district": "Gwanak-gu"},
    {"station_code": "231", "name_en": "Sindaebang", "name_kr": "신대방", "line": "Line 2", "latitude": 37.487462, "longitude": 126.913149, "district": "Dongjak-gu"},
    {"station_code": "232", "name_en": "Guro Digital Complex", "name_kr": "구로디지털단지", "line": "Line 2", "latitude": 37.485266, "longitude": 126.901401, "district": "Guro-gu"},
    {"station_code": "233", "name_en": "Daerim", "name_kr": "대림", "line": "Line 2", "latitude": 37.492970, "longitude": 126.895801, "district": "Yeongdeungpo-gu"},
    {"station_code": "234", "name_en": "Sindorim (L2)", "name_kr": "신도림 (2호선)", "line": "Line 2", "latitude": 37.508815, "longitude": 126.891222, "district": "Guro-gu"},
    {"station_code": "235", "name_en": "Mullae", "name_kr": "문래", "line": "Line 2", "latitude": 37.517933, "longitude": 126.894760, "district": "Yeongdeungpo-gu"},
    {"station_code": "236", "name_en": "Yeongdeungpo-gu Office", "name_kr": "영등포구청", "line": "Line 2", "latitude": 37.525700, "longitude": 126.896620, "district": "Yeongdeungpo-gu"},
    {"station_code": "237", "name_en": "Dangsan", "name_kr": "당산", "line": "Line 2", "latitude": 37.534380, "longitude": 126.902281, "district": "Yeongdeungpo-gu"},
    {"station_code": "238", "name_en": "Hapjeong", "name_kr": "합정", "line": "Line 2", "latitude": 37.549463, "longitude": 126.913739, "district": "Mapo-gu"},
    {"station_code": "239", "name_en": "Hongik Univ.", "name_kr": "홍대입구", "line": "Line 2", "latitude": 37.557192, "longitude": 126.925381, "district": "Mapo-gu"},
    {"station_code": "240", "name_en": "Sinchon", "name_kr": "신촌", "line": "Line 2", "latitude": 37.555134, "longitude": 126.936893, "district": "Seodaemun-gu"},
    {"station_code": "241", "name_en": "Ewha Womans Univ.", "name_kr": "이대", "line": "Line 2", "latitude": 37.556733, "longitude": 126.946013, "district": "Seodaemun-gu"},
    {"station_code": "242", "name_en": "Ahyeon", "name_kr": "아현", "line": "Line 2", "latitude": 37.557345, "longitude": 126.956141, "district": "Mapo-gu"},
    {"station_code": "243", "name_en": "Chungjeongno", "name_kr": "충정로", "line": "Line 2", "latitude": 37.559973, "longitude": 126.963558, "district": "Seodaemun-gu"},

    # Line 3
    {"station_code": "310", "name_en": "Gyeongbokgung", "name_kr": "경복궁", "line": "Line 3", "latitude": 37.575762, "longitude": 126.973530, "district": "Jongno-gu"},
    {"station_code": "311", "name_en": "Anguk", "name_kr": "안국", "line": "Line 3", "latitude": 37.576477, "longitude": 126.985443, "district": "Jongno-gu"},
    {"station_code": "312", "name_en": "Chungmuro", "name_kr": "충무로", "line": "Line 3", "latitude": 37.561243, "longitude": 126.994280, "district": "Jung-gu"},
    {"station_code": "313", "name_en": "Dongguk Univ.", "name_kr": "동대입구", "line": "Line 3", "latitude": 37.559052, "longitude": 127.005607, "district": "Jung-gu"},
    {"station_code": "314", "name_en": "Yaksu", "name_kr": "약수", "line": "Line 3", "latitude": 37.552185, "longitude": 127.010620, "district": "Jung-gu"},
    {"station_code": "315", "name_en": "Oksu", "name_kr": "옥수", "line": "Line 3", "latitude": 37.540700, "longitude": 127.017800, "district": "Seongdong-gu"},
    {"station_code": "316", "name_en": "Apgujeong", "name_kr": "압구정", "line": "Line 3", "latitude": 37.526279, "longitude": 127.028448, "district": "Gangnam-gu"},
    {"station_code": "317", "name_en": "Sinsa", "name_kr": "신사", "line": "Line 3", "latitude": 37.516334, "longitude": 127.020363, "district": "Gangnam-gu"},
    {"station_code": "318", "name_en": "Express Bus Terminal", "name_kr": "고속터미널", "line": "Line 3", "latitude": 37.504810, "longitude": 127.004943, "district": "Seocho-gu"},
    {"station_code": "319", "name_en": "Nambu Bus Terminal", "name_kr": "남부터미널", "line": "Line 3", "latitude": 37.485013, "longitude": 127.016189, "district": "Seocho-gu"},
    {"station_code": "320", "name_en": "Yangjae", "name_kr": "양재", "line": "Line 3", "latitude": 37.484147, "longitude": 127.034631, "district": "Seocho-gu"},
    {"station_code": "321", "name_en": "Maebong", "name_kr": "매봉", "line": "Line 3", "latitude": 37.486947, "longitude": 127.046761, "district": "Gangnam-gu"},
    {"station_code": "322", "name_en": "Dogok", "name_kr": "도곡", "line": "Line 3", "latitude": 37.490922, "longitude": 127.055446, "district": "Gangnam-gu"},
    {"station_code": "323", "name_en": "Daechi", "name_kr": "대치", "line": "Line 3", "latitude": 37.494612, "longitude": 127.063642, "district": "Gangnam-gu"},
    {"station_code": "324", "name_en": "Suseo", "name_kr": "수서", "line": "Line 3", "latitude": 37.487370, "longitude": 127.101880, "district": "Gangnam-gu"},

    # Line 4
    {"station_code": "410", "name_en": "Hyehwa", "name_kr": "혜화", "line": "Line 4", "latitude": 37.582336, "longitude": 127.001844, "district": "Jongno-gu"},
    {"station_code": "411", "name_en": "Myeong-dong", "name_kr": "명동", "line": "Line 4", "latitude": 37.560989, "longitude": 126.986325, "district": "Jung-gu"},
    {"station_code": "412", "name_en": "Hoehyeon", "name_kr": "회현", "line": "Line 4", "latitude": 37.558514, "longitude": 126.978246, "district": "Jung-gu"},
    {"station_code": "413", "name_en": "Sookmyung Women's Univ.", "name_kr": "숙대입구", "line": "Line 4", "latitude": 37.545012, "longitude": 126.972105, "district": "Yongsan-gu"},
    {"station_code": "414", "name_en": "Samgakji", "name_kr": "삼각지", "line": "Line 4", "latitude": 37.534777, "longitude": 126.973110, "district": "Yongsan-gu"},
    {"station_code": "415", "name_en": "Ichon", "name_kr": "이촌", "line": "Line 4", "latitude": 37.522272, "longitude": 126.973908, "district": "Yongsan-gu"},
    {"station_code": "416", "name_en": "Dongjak", "name_kr": "동작", "line": "Line 4", "latitude": 37.502971, "longitude": 126.979306, "district": "Dongjak-gu"},
    {"station_code": "417", "name_en": "Chongshin Univ. (Isu)", "name_kr": "총신대입구(이수)", "line": "Line 4", "latitude": 37.486263, "longitude": 126.981989, "district": "Dongjak-gu"},

    # Line 5
    {"station_code": "510", "name_en": "Gimpo Int'l Airport", "name_kr": "김포공항", "line": "Line 5", "latitude": 37.562434, "longitude": 126.801058, "district": "Gangseo-gu"},
    {"station_code": "511", "name_en": "Kkachisan", "name_kr": "까치산", "line": "Line 5", "latitude": 37.531768, "longitude": 126.846683, "district": "Gangseo-gu"},
    {"station_code": "512", "name_en": "Mok-dong", "name_kr": "목동", "line": "Line 5", "latitude": 37.529761, "longitude": 126.864920, "district": "Yangcheon-gu"},
    {"station_code": "513", "name_en": "Omokgyo", "name_kr": "오목교", "line": "Line 5", "latitude": 37.524485, "longitude": 126.875181, "district": "Yangcheon-gu"},
    {"station_code": "514", "name_en": "Yeouido", "name_kr": "여의도", "line": "Line 5", "latitude": 37.521624, "longitude": 126.924191, "district": "Yeongdeungpo-gu"},
    {"station_code": "515", "name_en": "Yeouinaru", "name_kr": "여의나루", "line": "Line 5", "latitude": 37.527099, "longitude": 126.932845, "district": "Yeongdeungpo-gu"},
    {"station_code": "516", "name_en": "Mapo", "name_kr": "마포", "line": "Line 5", "latitude": 37.539652, "longitude": 126.945929, "district": "Mapo-gu"},
    {"station_code": "517", "name_en": "Gongdeok", "name_kr": "공덕", "line": "Line 5", "latitude": 37.544487, "longitude": 126.951512, "district": "Mapo-gu"},
    {"station_code": "518", "name_en": "Gwanghwamun", "name_kr": "광화문", "line": "Line 5", "latitude": 37.571552, "longitude": 126.976553, "district": "Jongno-gu"},

    # Line 6
    {"station_code": "610", "name_en": "World Cup Stadium", "name_kr": "월드컵경기장", "line": "Line 6", "latitude": 37.569532, "longitude": 126.899083, "district": "Mapo-gu"},
    {"station_code": "611", "name_en": "Digital Media City", "name_kr": "디지털미디어시티", "line": "Line 6", "latitude": 37.577222, "longitude": 126.901389, "district": "Eunpyeong-gu"},
    {"station_code": "612", "name_en": "Mangwon", "name_kr": "망원", "line": "Line 6", "latitude": 37.556094, "longitude": 126.910052, "district": "Mapo-gu"},
    {"station_code": "613", "name_en": "Sangsu", "name_kr": "상수", "line": "Line 6", "latitude": 37.547781, "longitude": 126.922904, "district": "Mapo-gu"},
    {"station_code": "614", "name_en": "Gwangheungchang", "name_kr": "광흥창", "line": "Line 6", "latitude": 37.547456, "longitude": 126.931993, "district": "Mapo-gu"},
    {"station_code": "615", "name_en": "Daeheung", "name_kr": "대흥", "line": "Line 6", "latitude": 37.547771, "longitude": 126.942251, "district": "Mapo-gu"},
    {"station_code": "616", "name_en": "Hyochang Park", "name_kr": "효창공원앞", "line": "Line 6", "latitude": 37.539261, "longitude": 126.961351, "district": "Yongsan-gu"},
    {"station_code": "617", "name_en": "Noksapyeong", "name_kr": "녹사평", "line": "Line 6", "latitude": 37.534675, "longitude": 126.986695, "district": "Yongsan-gu"},
    {"station_code": "618", "name_en": "Itaewon", "name_kr": "이태원", "line": "Line 6", "latitude": 37.534533, "longitude": 126.994770, "district": "Yongsan-gu"},
    {"station_code": "619", "name_en": "Hangangjin", "name_kr": "한강진", "line": "Line 6", "latitude": 37.539655, "longitude": 127.001725, "district": "Yongsan-gu"},

    # Line 7
    {"station_code": "710", "name_en": "Nowon", "name_kr": "노원", "line": "Line 7", "latitude": 37.655128, "longitude": 127.061368, "district": "Nowon-gu"},
    {"station_code": "711", "name_en": "Taereung", "name_kr": "태릉입구", "line": "Line 7", "latitude": 37.618170, "longitude": 127.075055, "district": "Nowon-gu"},
    {"station_code": "712", "name_en": "Cheongdam", "name_kr": "청담", "line": "Line 7", "latitude": 37.519361, "longitude": 127.053535, "district": "Gangnam-gu"},
    {"station_code": "713", "name_en": "Gangnam-gu Office", "name_kr": "강남구청", "line": "Line 7", "latitude": 37.517179, "longitude": 127.041280, "district": "Gangnam-gu"},
    {"station_code": "714", "name_en": "Hak-dong", "name_kr": "학동", "line": "Line 7", "latitude": 37.514287, "longitude": 127.031648, "district": "Gangnam-gu"},
    {"station_code": "715", "name_en": "Nonhyeon", "name_kr": "논현", "line": "Line 7", "latitude": 37.511099, "longitude": 127.021415, "district": "Gangnam-gu"},
    {"station_code": "716", "name_en": "Banpo", "name_kr": "반포", "line": "Line 7", "latitude": 37.508178, "longitude": 127.011740, "district": "Seocho-gu"},
    {"station_code": "717", "name_en": "Naebang", "name_kr": "내방", "line": "Line 7", "latitude": 37.487618, "longitude": 126.992688, "district": "Seocho-gu"},
    {"station_code": "718", "name_en": "Boramae", "name_kr": "보라매", "line": "Line 7", "latitude": 37.499872, "longitude": 126.920428, "district": "Dongjak-gu"},
    {"station_code": "719", "name_en": "Gasan Digital Complex", "name_kr": "가산디지털단지", "line": "Line 7", "latitude": 37.480338, "longitude": 126.882656, "district": "Geumcheon-gu"},

    # Line 8
    {"station_code": "810", "name_en": "Amsa", "name_kr": "암사", "line": "Line 8", "latitude": 37.550210, "longitude": 127.127530, "district": "Gangdong-gu"},
    {"station_code": "811", "name_en": "Cheonho", "name_kr": "천호", "line": "Line 8", "latitude": 37.538740, "longitude": 127.123470, "district": "Gangdong-gu"},
    {"station_code": "812", "name_en": "Gangdong-gu Office", "name_kr": "강동구청", "line": "Line 8", "latitude": 37.530341, "longitude": 127.120508, "district": "Gangdong-gu"},
    {"station_code": "813", "name_en": "Mongchontoseong", "name_kr": "몽촌토성", "line": "Line 8", "latitude": 37.517409, "longitude": 127.112982, "district": "Songpa-gu"},
    {"station_code": "814", "name_en": "Seokchon", "name_kr": "석촌", "line": "Line 8", "latitude": 37.505431, "longitude": 127.106979, "district": "Songpa-gu"},
    {"station_code": "815", "name_en": "Songpa", "name_kr": "송파", "line": "Line 8", "latitude": 37.499703, "longitude": 127.112196, "district": "Songpa-gu"},
    {"station_code": "816", "name_en": "Garak Market", "name_kr": "가락시장", "line": "Line 8", "latitude": 37.492522, "longitude": 127.118234, "district": "Songpa-gu"},
    {"station_code": "817", "name_en": "Munjeong", "name_kr": "문정", "line": "Line 8", "latitude": 37.485890, "longitude": 127.122501, "district": "Songpa-gu"},
    {"station_code": "818", "name_en": "Jangji", "name_kr": "장지", "line": "Line 8", "latitude": 37.478703, "longitude": 127.126191, "district": "Songpa-gu"},
    {"station_code": "819", "name_en": "Bokjeong", "name_kr": "복정", "line": "Line 8", "latitude": 37.470023, "longitude": 127.126662, "district": "Songpa-gu"},

    # Line 9
    {"station_code": "910", "name_en": "National Assembly", "name_kr": "국회의사당", "line": "Line 9", "latitude": 37.528105, "longitude": 126.917415, "district": "Yeongdeungpo-gu"},
    {"station_code": "911", "name_en": "Saetgang", "name_kr": "샛강", "line": "Line 9", "latitude": 37.517277, "longitude": 126.928422, "district": "Yeongdeungpo-gu"},
    {"station_code": "912", "name_en": "Nodeul", "name_kr": "노들", "line": "Line 9", "latitude": 37.512887, "longitude": 126.953851, "district": "Dongjak-gu"},
    {"station_code": "913", "name_en": "Heukseok", "name_kr": "흑석", "line": "Line 9", "latitude": 37.508758, "longitude": 126.963708, "district": "Dongjak-gu"},
    {"station_code": "914", "name_en": "Gubanpo", "name_kr": "구반포", "line": "Line 9", "latitude": 37.501362, "longitude": 126.987332, "district": "Seocho-gu"},
    {"station_code": "915", "name_en": "Sinbanpo", "name_kr": "신반포", "line": "Line 9", "latitude": 37.503430, "longitude": 126.995925, "district": "Seocho-gu"},
    {"station_code": "916", "name_en": "Sinnonhyeon", "name_kr": "신논현", "line": "Line 9", "latitude": 37.504598, "longitude": 127.025060, "district": "Gangnam-gu"},
    {"station_code": "917", "name_en": "Eonju", "name_kr": "언주", "line": "Line 9", "latitude": 37.507287, "longitude": 127.033877, "district": "Gangnam-gu"},
    {"station_code": "918", "name_en": "Seonjeongneung", "name_kr": "선정릉", "line": "Line 9", "latitude": 37.510297, "longitude": 127.043999, "district": "Gangnam-gu"},
    {"station_code": "919", "name_en": "Samseong Jungang", "name_kr": "삼성중앙", "line": "Line 9", "latitude": 37.513011, "longitude": 127.053282, "district": "Gangnam-gu"},
    {"station_code": "920", "name_en": "Bongeunsa", "name_kr": "봉은사", "line": "Line 9", "latitude": 37.514219, "longitude": 127.060203, "district": "Gangnam-gu"},
]


def compute_ridership_gaussian_curve(hour: int, is_weekend: bool, is_business_district: bool = True) -> tuple[float, float]:
    """
    Computes mathematical double-Gaussian curve weights for realistic Seoul Metro hourly volume.
    
    Formula:
      Weekday Inflow:
        G_am = 1.25 * exp(-((h - 8.2)^2) / (2 * 1.25^2))
        G_pm = 0.95 * exp(-((h - 18.5)^2) / (2 * 1.4^2))
        Base = 0.22 (lunch/midday plateaus at ~0.45)
        LateNight = 0.02
      Weekend:
        G_wknd = 0.85 * exp(-((h - 15.0)^2) / (2 * 3.5^2))
        Base = 0.15
    """
    if not is_weekend:
        # Morning peak (centered at 8:15 AM)
        g_am_in = 1.35 * math.exp(-((hour - 8.2) ** 2) / (2 * (1.2 ** 2)))
        g_am_out = 1.45 * math.exp(-((hour - 8.5) ** 2) / (2 * (1.1 ** 2))) if is_business_district else 0.75 * math.exp(-((hour - 8.2) ** 2) / (2 * (1.2 ** 2)))

        # Evening peak (centered at 18:30 PM)
        g_pm_in = 1.40 * math.exp(-((hour - 18.3) ** 2) / (2 * (1.3 ** 2))) if is_business_district else 0.80 * math.exp(-((hour - 18.5) ** 2) / (2 * (1.4 ** 2)))
        g_pm_out = 1.50 * math.exp(-((hour - 18.6) ** 2) / (2 * (1.3 ** 2)))

        # Midday lunch plateau (11:30 - 13:30)
        g_mid = 0.35 * math.exp(-((hour - 12.5) ** 2) / (2 * (1.5 ** 2)))

        # Late-night dropoff (00:00 - 05:00)
        if 0 <= hour <= 4:
            base = 0.015
        elif hour == 5 or hour == 23:
            base = 0.12
        else:
            base = 0.22

        inflow_weight = max(0.01, base + g_am_in + g_pm_in + g_mid)
        outflow_weight = max(0.01, base + g_am_out + g_pm_out + g_mid)
    else:
        # Weekend: Unimodal afternoon leisure & shopping curve (peak ~15:00)
        g_wknd = 0.88 * math.exp(-((hour - 15.2) ** 2) / (2 * (3.6 ** 2)))
        
        if 0 <= hour <= 5:
            base = 0.02
        elif hour == 6 or hour == 23:
            base = 0.10
        else:
            base = 0.18

        inflow_weight = max(0.01, base + g_wknd)
        outflow_weight = max(0.01, base + g_wknd * random.uniform(0.95, 1.05))

    return inflow_weight, outflow_weight


def seed_database(db: Session, force: bool = False):
    print("\n=======================================================")
    print("       METROFLOW DATABASE SEEDING ENGINE (PHASE 1)      ")
    print("=======================================================")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    inserted_counts = {
        "stations": 0,
        "ridership_logs": 0,
        "train_status": 0,
        "alerts": 0,
    }

    # 1. Seed Stations
    print("\n[1/4] Processing stations inventory...")
    existing_stations = db.execute(select(Station)).scalars().all()
    existing_station_map = {s.station_code: s for s in existing_stations}
    
    stations_to_insert = []
    csv_paths = [
        Path("stations_clean.csv"),
        Path("../stations_clean.csv"),
        Path(__file__).resolve().parent.parent.parent / "stations_clean.csv",
    ]
    csv_found = None
    for p in csv_paths:
        if p.exists():
            csv_found = p
            break

    if csv_found:
        print(f"      Loading from clean CSV dataset: {csv_found}")
        df = pd.read_csv(csv_found)
        for _, row in df.iterrows():
            st_code = str(row.get("station_code", row.get("code", ""))).strip()
            name_en = str(row.get("name_en", row.get("name", ""))).strip()
            name_kr_val = row.get("name_kr")
            name_kr = str(name_kr_val).strip() if pd.notna(name_kr_val) else None
            line = str(row.get("line", "Line 1")).strip()
            lat = float(row.get("latitude", row.get("lat", 37.55)))
            lng = float(row.get("longitude", row.get("lng", 126.97)))
            district_val = row.get("district")
            district = str(district_val).strip() if pd.notna(district_val) else None

            stations_to_insert.append({
                "station_code": st_code,
                "name_en": name_en,
                "name_kr": name_kr,
                "line": line,
                "latitude": lat,
                "longitude": lng,
                "district": district,
            })
    else:
        print(f"      Using built-in Seoul Metro network ({len(SEOUL_STATIONS_DEFAULT)} stations)")
        stations_to_insert = SEOUL_STATIONS_DEFAULT

    new_stations = []
    for st_data in stations_to_insert:
        if st_data["station_code"] not in existing_station_map:
            new_station = Station(**st_data)
            new_stations.append(new_station)
            existing_station_map[st_data["station_code"]] = new_station

    if new_stations:
        db.add_all(new_stations)
        db.commit()
        inserted_counts["stations"] = len(new_stations)
        print(f"      Inserted {len(new_stations)} new stations.")
    else:
        print(f"      Station inventory already up to date ({len(existing_stations)} stations).")

    all_stations = list(existing_station_map.values())

    # 2. Seed Ridership Logs (Last 14 days of realistic hourly curves)
    print("\n[2/4] Generating synthetic ridership time-series logs...")
    existing_ridership_count = db.execute(select(func.count(RidershipLog.id))).scalar() or 0

    if existing_ridership_count == 0 or force:
        now = datetime.now(timezone.utc)
        # Generate 14 days of hourly records
        num_days = 14
        start_time = (now - timedelta(days=num_days)).replace(minute=0, second=0, microsecond=0)
        total_hours = num_days * 24

        major_hubs = {"150", "222", "239", "216", "318", "1004", "514", "208", "212", "916"}
        business_districts = {"Gangnam-gu", "Jung-gu", "Yeongdeungpo-gu", "Jongno-gu"}

        records = []
        batch_size = 2500
        total_seeded_ridership = 0

        for station in all_stations:
            base_capacity = 3600 if station.station_code in major_hubs else 1200
            is_business = station.district in business_districts if station.district else False

            for i in range(total_hours):
                current_dt = start_time + timedelta(hours=i)
                dow = current_dt.weekday()  # 0=Mon, 6=Sun
                hr = current_dt.hour
                is_wknd = dow >= 5

                in_weight, out_weight = compute_ridership_gaussian_curve(hr, is_wknd, is_business)

                # Stochastic variance
                noise_in = random.uniform(0.90, 1.10)
                noise_out = random.uniform(0.90, 1.10)

                inflow = max(5, int(base_capacity * in_weight * noise_in))
                outflow = max(5, int(base_capacity * out_weight * noise_out))

                record = RidershipLog(
                    station_code=station.station_code,
                    timestamp=current_dt,
                    hour=hr,
                    day_of_week=dow,
                    is_weekend=is_wknd,
                    inflow=inflow,
                    outflow=outflow,
                )
                records.append(record)

                if len(records) >= batch_size:
                    db.add_all(records)
                    db.commit()
                    total_seeded_ridership += len(records)
                    records = []

        if records:
            db.add_all(records)
            db.commit()
            total_seeded_ridership += len(records)

        inserted_counts["ridership_logs"] = total_seeded_ridership
        print(f"      Inserted {total_seeded_ridership:,} hourly ridership records.")
    else:
        print(f"      Ridership records already present ({existing_ridership_count:,} rows).")

    # 3. Seed Train Status
    print("\n[3/4] Generating train telemetry status records...")
    existing_trains_count = db.execute(select(func.count(TrainStatus.id))).scalar() or 0

    if existing_trains_count == 0 or force:
        lines = [f"Line {i}" for i in range(1, 10)]
        now = datetime.now(timezone.utc)
        train_records = []

        # Generate telemetry points across the last 24 hours (every 15 min per line)
        intervals = 24 * 4  # 96 points per line
        for line_name in lines:
            for offset in range(intervals, -1, -1):
                ts = now - timedelta(minutes=offset * 15)
                hr = ts.hour
                is_wknd = ts.weekday() >= 5
                
                # Correlate occupancy with curve
                in_w, _ = compute_ridership_gaussian_curve(hr, is_wknd)
                occupancy = min(100.0, max(15.0, round(25.0 + 70.0 * in_w + random.uniform(-4.0, 4.0), 1)))
                
                # 5% probability of operational delay
                delay = random.randint(2, 9) if random.random() < 0.05 else 0

                train_st = TrainStatus(
                    line=line_name,
                    timestamp=ts,
                    occupancy_pct=occupancy,
                    delay_minutes=delay,
                )
                train_records.append(train_st)

        db.add_all(train_records)
        db.commit()
        inserted_counts["train_status"] = len(train_records)
        print(f"      Inserted {len(train_records):,} train telemetry records.")
    else:
        print(f"      Train telemetry already present ({existing_trains_count:,} rows).")

    # 4. Seed Alerts
    print("\n[4/4] Populating active and historic alerts...")
    existing_alerts_count = db.execute(select(func.count(Alert.id))).scalar() or 0

    if existing_alerts_count == 0 or force:
        now = datetime.now(timezone.utc)
        sample_alerts = [
            {
                "station_code": "222",  # Gangnam
                "alert_type": "overcrowding",
                "severity": "critical",
                "message": "Platform density exceeded 185 passengers/sqm at Line 2 transfer concourse.",
                "created_at": now - timedelta(minutes=18),
                "resolved": False,
            },
            {
                "station_code": "239",  # Hongik Univ.
                "alert_type": "overcrowding",
                "severity": "high",
                "message": "Heavy entry bottleneck detected at Exit 9.",
                "created_at": now - timedelta(minutes=42),
                "resolved": False,
            },
            {
                "station_code": "150",  # Seoul Station
                "alert_type": "delay",
                "severity": "medium",
                "message": "Line 1 dispatch headway widened due to track signal regulation.",
                "created_at": now - timedelta(hours=1, minutes=15),
                "resolved": False,
            },
            {
                "station_code": "216",  # Jamsil
                "alert_type": "overcrowding",
                "severity": "high",
                "message": "Transfer corridor Line 2/8 congestion cleared.",
                "created_at": now - timedelta(hours=3),
                "resolved": True,
            },
            {
                "station_code": "514",  # Yeouido
                "alert_type": "delay",
                "severity": "low",
                "message": "Platform screen door sync delay resolved.",
                "created_at": now - timedelta(hours=5),
                "resolved": True,
            },
        ]

        alerts_to_add = []
        for a in sample_alerts:
            if a["station_code"] in existing_station_map:
                alerts_to_add.append(Alert(**a))

        db.add_all(alerts_to_add)
        db.commit()
        inserted_counts["alerts"] = len(alerts_to_add)
        print(f"      Inserted {len(alerts_to_add)} sample alerts.")
    else:
        print(f"      Alerts already present ({existing_alerts_count} rows).")

    # 5. Populate Default Users
    from app.models.user import User
    from app.core.security import get_password_hash
    print("\n[5/5] Populating default operator and admin accounts...")
    existing_users = {u.username: u for u in db.execute(select(User)).scalars().all()}
    
    default_users = [
        {"username": "operator", "password": "operatorpassword", "role": "operator"},
        {"username": "operator123", "password": "operator123", "role": "operator"},
        {"username": "admin", "password": "adminpassword", "role": "admin"},
        {"username": "admin123", "password": "admin123", "role": "admin"},
        {"username": "station_manager", "password": "adminpassword", "role": "admin"},
    ]

    new_users = []
    for u in default_users:
        if u["username"] not in existing_users:
            new_users.append(User(
                username=u["username"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"]
            ))
            existing_users[u["username"]] = True

    if new_users:
        db.add_all(new_users)
        db.commit()
        inserted_counts["users"] = len(new_users)
        print(f"      Inserted {len(new_users)} default user accounts.")
    else:
        print(f"      Default users already exist ({len(existing_users)} users).")

    # Summary table
    print("\n=======================================================")
    print("                 SEEDING SUMMARY REPORT                ")
    print("=======================================================")
    total_stations = db.execute(select(func.count(Station.station_code))).scalar()
    total_ridership = db.execute(select(func.count(RidershipLog.id))).scalar()
    total_trains = db.execute(select(func.count(TrainStatus.id))).scalar()
    total_alerts = db.execute(select(func.count(Alert.id))).scalar()
    total_users = db.execute(select(func.count(User.id))).scalar()

    print(f"  Stations In DB:       {total_stations:>8,}  (New: {inserted_counts.get('stations', 0)})")
    print(f"  Ridership Logs In DB: {total_ridership:>8,}  (New: {inserted_counts.get('ridership_logs', 0)})")
    print(f"  Train Status Logs:    {total_trains:>8,}  (New: {inserted_counts.get('train_status', 0)})")
    print(f"  Alerts In DB:         {total_alerts:>8,}  (New: {inserted_counts.get('alerts', 0)})")
    print(f"  Users In DB:          {total_users:>8,}  (New: {inserted_counts.get('users', 0)})")
    print("=======================================================\n")


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_database(session)
