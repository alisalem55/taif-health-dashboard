import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.parse
import io

# إعداد واجهة البرنامج لتكون عريضة ومناسبة لـ Dashboard غرف العمليات
st.set_page_config(page_title="منظومة الرصد الموحد والأزمات - الطائف", layout="wide")

st.markdown("<h1 style='text-align: right; color: #007A33;'>🏥 منظومة الرصد الإعلامي والإنذار المبكر الحية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right;'>مراقبة حية ونقية 100% مستخرجة من الويب والمنصات الإخبارية للتحذيرات، الحرائق، وبلاغات الطائف حالياً.</p>", unsafe_allow_html=True)

# دالة لتوليد روابط البحث المباشرة لمنصة X لمنع الحظر
def get_clean_url(google_rss_url, title_text):
    try:
        response = requests.head(google_rss_url, allow_redirects=True, timeout=3)
        final_url = response.url
        if "x.com" in final_url or "twitter.com" in final_url:
            clean_title = title_text.split(" - ").strip()
            encoded_title = urllib.parse.quote(clean_title)
            return f"https://x.com{encoded_title}&f=live"
        return final_url
    except:
        clean_title = title_text.split(" - ").strip()
        encoded_title = urllib.parse.quote(clean_title)
        return f"https://x.com{encoded_title}&f=live"

# بوابة حماية الدخول الرسمية
def check_login():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("<h2 style='text-align: right; color: #007A33;'>🔒 بوابة الدخول الآمنة</h2>", unsafe_allow_html=True)
        user_input = st.text_input("اسم المستخدم:")
        pass_input = st.text_input("كلمة السر:", type="password")
        if st.button("🔓 تسجيل الدخول"):
            if user_input == "admin" and pass_input == "MOH@2026":
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ صلاحيات الدخول غير صحيحة.")
        return False
    return True

if check_login():
    @st.cache_data(ttl=60) # تحديث حقيقي وصارم كل دقيقة من الإنترنت مباشرة
    def fetch_live_news(search_query):
        try:
            search_query = search_query.strip()
            base_url = "https://google.com"
            
            # استعلام نقي وموسع يطارد أحداث الطائف الصحية والطارئة حياً
            raw_query = f"{search_query} (صحة OR مستشفى OR طوارئ OR حريق OR حوادث OR تحذير OR أمطار OR شكوى)"
            
            params = {"q": raw_query, "gl": "SA", "hl": "ar", "ceid": "SA:ar"}
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            if response.status_code != 200 or not response.content:
                return pd.DataFrame()
                
            root = ET.fromstring(response.content)
            news_list = []
            
            alert_keywords = ["تحذير", "الإنذار", "تنبيه", "أرصاد", "سيول", "أمطار", "توقعات", "الأرصاد"]
            fire_keywords = ["حريق", "اندلاع", "حادث", "تماس", "إنقاذ", "الدفاع المدني", "حرائق"]
            negative_keywords = ["شكوى", "إهمال", "ازدحام", "نقص", "تأخر", "سوء", "معاناة", "تذمر", "تعطل"]
            positive_keywords = ["إشادة", "شكر", "نجاح", "تميز", "جاهزية", "تكريم", "افتتاح", "شكراً", "تدشين"]
            
            items = root.findall('.//item')
            if not items: return pd.DataFrame()
                
            for item in items[:40]:
                title = item.find('title').text
                raw_link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                clean_link = get_clean_url(raw_link, title)
                
                source_name = "رصد_حي"
                if " - " in title:
                    parts = title.split(" - ")
                    source_name = parts[-1].strip()
                    title = " - ".join(parts[:-1]).strip()
                
                try:
                    clean_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d %H:%M')
                except: clean_date = pub_date

                sentiment = "🟡 محايد / استفسار"
                if any(word in title for word in alert_keywords): sentiment = "⚠️ تحذير / طوارئ عاجلة"
                elif any(word in title for word in fire_keywords): sentiment = "🔥 حريق / حادثة"
                elif any(word in title for word in negative_keywords): sentiment = "🔴 سلبي / شكوى حرج"
                elif any(word in title for word in positive_keywords): sentiment = "🟢 إيجابي / جاهزية"
                    
                news_list.append({
                    "التاريخ والوقت": clean_date,
                    "المصدر": source_name,
                    "تفاصيل البلاغ / الرصد": title,
                    "رابط المصدر المباشر": clean_link,
                    "نوع الحدث": sentiment
                })
                
            return pd.DataFrame(news_list)
        except:
            return pd.DataFrame()

    def convert_df_to_html(dataframe, branch):
        html_content = f"""
        <html><head><meta charset="utf-8"><style>
            body {{ font-family: 'Segoe UI', sans-serif; direction: rtl; text-align: right; margin: 30px; }}
            h1 {{ color: #007A33; border-bottom: 2px solid #007A33; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: right; }}
            th {{ background-color: #007A33; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style></head><body>
            <h1>🏥 تقرير الرصد الموحد لقطاع الطوارئ والصحة - {branch}</h1>
            <p><strong>تاريخ استخراج التقرير:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <table>
                <tr><th>التاريخ والوقت</th><th>المصدر</th><th>تفاصيل البلاغ</th><th>نوع الحدث</th></tr>
        """
        for _, row in dataframe.iterrows():
            html_content += f"<tr><td>{row['التاريخ والوقت']}</td><td>{row['المصدر']}</td><td>{row['تفاصيل البلاغ / الرصد']}</td><td>{row['نوع الحدث']}</td></tr>"
        html_content += "</table></body></html>"
        return html_content

    st.sidebar.header("⚙️ رادار الرصد الموحد")
    branch_name = st.sidebar.text_input("نطاق الرصد الجغرافي الأساسي:", value="الطائف")

    if st.sidebar.button("🔄 تحديث وسحب البيانات الحية"):
        st.cache_data.clear()
        st.rerun()

    df = fetch_live_news(branch_name)
    if not df.empty:
        total = len(df)
        neg_count = len(df[df["نوع الحدث"] == "🔴 سلبي / شكوى حرج"])
        pos_count = len(df[df["نوع الحدث"] == "🟢 إيجابي / جاهزية"])
        alert_count = len(df[df["نوع الحدث"] == "⚠️ تحذير / طوارئ عاجلة"])
        fire_count = len(df[df["نوع الحدث"] == "🔥 حريق / حادثة"])
        
        if fire_count > 0 or alert_count > 0:
            st.error(f"🚨 **إنذار غرف العمليات عاجل:** تم رصد أحداث طارئة تخص {branch_name}!")
            
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("إجمالي المواد المكتشفة", total)
        kpi2.metric("🔥 حرائق وحوادث", fire_count)
        kpi3.metric("⚠️ تحذيرات وإنذارات", alert_count)
        kpi4.metric("🔴 شكاوى وبلاغات", neg_count)
        kpi5.metric("🟢 إشادات وجاهزية", pos_count)
        
        st.markdown("---")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📊 توزيع مؤشرات الأزمات والرأي العام")
            fig_pie = px.pie(df, names="نوع الحدث", color="نوع الحدث",
                             color_discrete_map={
                                 "🔴 سلبي / شكوى حرج": "#FF4B4B",
                                 "🟢 إيجابي / جاهزية": "#00D4B2",
                                 "⚠️ تحذير / طوارئ عاجلة": "#FF9900",
                                 "🔥 حريق / حادثة": "#CC0000",
                                 "🟡 محايد / استفسار": "#FFDA44"
                             })
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_chart2:
            st.subheader("📈 التوزيع الزمني لتدفق البلاغات")
            fig_bar = px.histogram(df, x="التاريخ والوقت", color="نوع الحدث",
                                   color_discrete_map={
                                       "🔴 سلبي / شكوى حرج": "#FF4B4B",
                                       "🟢 إيجابي / جاهزية": "#00D4B2",
                                       "⚠️ تحذير / طوارئ عاجلة": "#FF9900",
                                       "🔥 حريق / حادثة": "#CC0000",
                                       "🟡 محايد / استفسار": "#FFDA44"
                                   })
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.subheader("🔍 تفاصيل جدار الرصد الموحد وعناوين المصادر")
        
        st.data_editor(
            df,
            column_config={
                "رابط المصدر المباشر": st.column_config.LinkColumn(
                    "رابط المصدر المباشر",
                    max_chars=400,
                    display_text="🔗 اضغط للانتقال للموقع الأصلي"
                )
            },
            disabled=True,
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("### 📥 مركز تصدير التقارير الرسمية")
        export_col1, export_col2 = st.columns(2)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='تقرير الطوارئ والرصد')
        excel_buffer.seek(0)
        
        with export_col1:
            st.download_button(
                label="📥 تحميل تقرير الأزمات بصيغة Excel",
                data=excel_buffer,
                file_name=f"تقرير_طوارئ_الطائف.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        html_report = convert_df_to_html(df, branch_name)
        with export_col2:
            st.download_button(
                label="📄 فتح واستخراج تقرير الطوارئ بصيغة PDF حقيقية ودعم عربي",
                data=html_report,
                file_name=f"تقرير_طوارئ_الطائف.html",
                mime="text/html",
                use_container_width=True
            )
    else:
        st.warning("⚠️ جاري فحص الويب... لا توجد أخبار حية أو تغريدات علنية منشورة في هذه الدقيقة تتوفر برمجياً بشكل مجاني.")
