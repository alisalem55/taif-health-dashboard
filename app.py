import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import urllib.parse
import io
import time

# إعداد واجهة البرنامج لتكون عريضة ومناسبة لـ Dashboard غرف العمليات
st.set_page_config(page_title="منظومة الرصد الموحد والأزمات - الطائف", layout="wide")

st.markdown("<h1 style='text-align: right; color: #007A33;'>📱 رادار الرصد الحي والإنذار المبكر - الطائف</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: right;'>مراقبة حية وشاملة للبلاغات، الحرائق، وتغريدات الطائف الحقيقية المرفوعة عبر مستودعك الآمن.</p>", unsafe_allow_html=True)

# دالة لتوليد روابط البحث المباشرة لمنصة X لمنع الحظر
def get_clean_url(title_text):
    clean_title = title_text.strip()
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
    @st.cache_data(ttl=1)  # خفض مدة الكاش إلى ثانية واحدة لإجبار المتصفح على جلب الملف فوراً
    def fetch_health_news(search_query):
        try:
            # استخدام الرابط المباشر للملف مع إضافة كود الوقت لمنع الكاش نهائياً وتخطي حظر السيرفرات
            timestamp = int(time.time())
            url = f"https://githubusercontent.com{timestamp}"
            
            headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return pd.DataFrame()
                
            df_raw = pd.read_csv(io.StringIO(response.text), encoding='utf-8')
            
            news_list = []
            for _, row in df_raw.iterrows():
                title = str(row.get("المنشور", ""))
                source_name = str(row.get("المصدر", "رصد_حقيقي"))
                pub_date = str(row.get("التاريخ", datetime.now().strftime('%Y-%m-%d %H:%M')))
                sentiment = str(row.get("نوع الحدث", "🟡 محايد / استفسار"))
                
                news_list.append({
                    "التاريخ والوقت": pub_date,
                    "اسم المغرد / المصدر": source_name,
                    "المنشور / رصد منصة X": title,
                    "رابط المصدر المباشر": get_clean_url(title),
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
        
        # استخدام ميزة LinkColumn للتوجه المباشر إلى البحث التلقائي الفوري عن التغريدة داخل إكس لفك التشفير بناءً على النص الفعلي
        st.data_editor(
            filtered_df,
            column_config={
                "رابط المصدر المباشر": st.column_config.LinkColumn(
                    "رابط المصدر المباشر",
                    help="اضغط هنا للتوجه إلى البحث التلقائي الفوري عن التغريدة داخل إكس لفك التشفير بناءً على النص الفعلي",
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
