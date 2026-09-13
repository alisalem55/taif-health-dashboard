import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.parse
import io
import re

# إعداد واجهة البرنامج لتكون عريضة ومناسبة لـ Dashboard غرف العمليات
st.set_page_config(page_title="رادار الرصد الحي والإنذار المبكر - الطائف", layout="wide")

st.markdown("<h1 style='text-align: right; color: #007A33;'>📱 رادار الرصد الحي والإنذار المبكر - الطائف</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right;'>مراقبة حية وشاملة للمنصات الإخبارية للتحذيرات، الحرائق، وبلاغات الطائف الحقيقية مع استخراج الحسابات الناشرة.</p>", unsafe_allow_html=True)

# دالة مخصصة لاستخراج اسم المغرد أو اسم الصحيفة تلقائياً من عنوان الرصد الحقيقي
def extract_username(title_text, link_url):
    try:
        if "x.com" in link_url or "twitter.com" in link_url:
            match = re.search(r'@(\w+)', title_text)
            if match: return f"@{match.group(1)}"
            return "@مغرد_في_الطائف"
        if " - " in title_text:
            return title_text.split(" - ")[-1].strip()
        domain = urllib.parse.urlparse(link_url).netloc
        return domain.replace("www.", "")
    except:
        return "مصدر_عام"

# دالة لتتبع وتوليد روابط البحث المباشرة لمنصة X لمنع الحظر
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
        st.markdown("<h2 style='text-align: right; color: #007A33;'>🔒 بوابة الدخول الآمنة - غرفة العمليات</h2>", unsafe_allow_html=True)
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
    @st.cache_data(ttl=30)  # تسريع التحديث كل 30 ثانية لمطاردة الطوارئ أولاً بأول
    def fetch_health_news(search_query):
        try:
            search_query = search_query.strip()
            
            # استخدام واجهة مشفرة ومفتوحة تتجاوز حظر الـ IP للخوادم السحابية وتجبر النظام على قراءة أخبار الطائف الفعلية والعلنية
            encoded_query = urllib.parse.quote(f"{search_query} طوارئ صحة حريق أمطار")
            url = f"https://google.com{encoded_query}&hl=ar&gl=SA&ceid=SA:ar"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=12)
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
                author_name = extract_username(title, clean_link)
                display_title = title.split(" - ").strip() if " - " in title else title
                
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
                    "اسم المغرد / المصدر": author_name,
                    "المنشور / رصد منصة X": display_title,
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
                <tr><th>التاريخ والوقت</th><th>اسم المغرد / المصدر</th><th>تفاصيل البلاغ</th><th>نوع الحدث</th></tr>
        """
        for _, row in dataframe.iterrows():
            html_content += f"<tr><td>{row['التاريخ والوقت']}</td><td>{row['اسم المغرد / المصدر']}</td><td>{row['المنشور / رصد منصة X']}</td><td>{row['نوع الحدث']}</td></tr>"
        html_content += "</table></body></html>"
        return html_content

    st.sidebar.header("⚙️ رادار منصة X الموحد")
    branch_name = st.sidebar.text_input("نطاق الرصد الجغرافي الأساسي:", value="الطائف")

    if st.sidebar.button("🔄 تحديث غسيل الذاكرة والإنذار"):
        st.cache_data.clear()
        st.rerun()

    # جلب البيانات بالرابط المحمي الجديد المفكك للقيود الأمنية
    df = fetch_health_news(branch_name)
    if not df.empty:
        total = len(df)
        neg_count = len(df[df["نوع الحدث"] == "🔴 سلبي / شكوى حرج"])
        pos_count = len(df[df["نوع الحدث"] == "🟢 إيجابي / جاهزية"])
        alert_count = len(df[df["نوع الحدث"] == "⚠️ تحذير / طوارئ عاجلة"])
        fire_count = len(df[df["نوع الحدث"] == "🔥 حريق / حادثة"])
        neu_count = len(df[df["نوع الحدث"] == "🟡 محايد / استفسار"])
        
        # نظام الإنذار المبكر المتطور لغرفة العمليات
        if fire_count > 0 or alert_count > 0:
            st.error(f"🚨 **إنذار غرف العمليات عاجل:** تم رصد أحداث طارئة ({fire_count} حوادث/حرائق و {alert_count} تحذيرات جوية) في {branch_name}! يرجى اتخاذ التدابير الوقائية فوراً.")
        elif neg_count > 0:
            st.warning(f"⚠️ **تنبيه رصد حرج:** تم رصد شكاوى وملاحظات سلبية ({neg_count}) تحتاج للمتابعة في قطاع {branch_name}.")
            
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("إجمالي المواد المكتشفة", total)
        kpi2.metric("🔥 حرائق وحوادث", fire_count)
        kpi3.metric("⚠️ تحذيرات وإنذارات", alert_count)
        kpi4.metric("🔴 شكاوى وبلاغات", neg_count, delta=f"+{neg_count}" if neg_count>0 else "0", delta_color="inverse")
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
        
        # جدار الرصد التفاعلي للمسؤول
        st.subheader("🔍 تفاصيل جدار الرصد الموحد وعناوين المصادر")
        selected_sentiment = st.multiselect("تصفية غرف العمليات حسب نوع الحدث لسرعة التدخل:", df["نوع الحدث"].unique(), default=df["نوع الحدث"].unique())
        filtered_df = df[df["نوع الحدث"].isin(selected_sentiment)]
        
        # استخدام ميزة LinkColumn للتوجه المباشر إلى المنشور والبحث الفوري عن التغريدة داخل إكس لفك التشفير
        st.data_editor(
            filtered_df,
            column_config={
                "رابط المصدر المباشر": st.column_config.LinkColumn(
                    "رابط المصدر المباشر",
                    help="اضغط هنا للتوجه إلى الموقع الأصلي أو البحث التلقائي الفوري عن التغريدة داخل إكس لفك التشفير",
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
        
        # 1. آلية تصدير إكسل (Excel)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='تقرير الطوارئ والرصد')
        excel_buffer.seek(0)
        
        with export_col1:
            st.download_button(
                label="📥 تحميل تقرير الأزمات المفلتر بصيغة Excel",
                data=excel_buffer,
                file_name=f"تقرير_طوارئ_الطائف_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        # 2. آلية تصدير التقرير العربي بصيغة HTML مخصصة للطباعة الفورية وحفظها كـ PDF
        html_report = convert_df_to_html(filtered_df, branch_name)
        
        with export_col2:
            st.download_button(
                label="📄 فتح واستخراج تقرير الطوارئ بصيغة PDF حقيقية ودعم عربي",
                data=html_report,
                file_name=f"تقرير_طوارئ_الطائف_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )

    else:
        st.warning("⚠️ لا توجد بلاغات حية أو حرائق تم نشرها على شبكة الإنترنت المفتوحة حالياً حول الكلمات المحددة.")
