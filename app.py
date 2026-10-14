import streamlit as st
import mysql.connector
import pandas as pd


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Sales Management System",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sales_management_system"
    )


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

# ------------------------------------------------------------
# GET BRANCHES
# ------------------------------------------------------------

def get_branches():

    conn = get_connection()

    query = """
        SELECT
            branch_id,
            branch_name
        FROM branches
        ORDER BY branch_id
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ------------------------------------------------------------
# GET SALES
# ------------------------------------------------------------

def get_sales(branch_id=None, status=None):

    conn = get_connection()

    query = """
        SELECT
            cs.sale_id,
            cs.branch_id,
            b.branch_name,
            cs.date,
            cs.name,
            cs.mobile_number,
            cs.product_name,
            cs.gross_sales,
            cs.received_amount,
            cs.pending_amount,
            cs.status
        FROM customer_sales cs
        JOIN branches b
            ON cs.branch_id = b.branch_id
        WHERE 1 = 1
    """

    params = []

    if branch_id is not None:

        query += """
            AND cs.branch_id = %s
        """

        params.append(branch_id)

    if status is not None:

        query += """
            AND cs.status = %s
        """

        params.append(status)

    query += """
        ORDER BY cs.date DESC, cs.sale_id DESC
    """

    df = pd.read_sql(
        query,
        conn,
        params=tuple(params)
    )

    conn.close()

    return df


# ------------------------------------------------------------
# GET SALES SUMMARY
# ------------------------------------------------------------

def get_sales_summary(branch_id=None):

    conn = get_connection()

    query = """
        SELECT
            COUNT(*) AS total_sales,
            COALESCE(SUM(gross_sales), 0) AS total_gross_sales,
            COALESCE(SUM(received_amount), 0) AS total_received,
            COALESCE(SUM(pending_amount), 0) AS total_pending
        FROM customer_sales
    """

    params = []

    if branch_id is not None:

        query += """
            WHERE branch_id = %s
        """

        params.append(branch_id)

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        query,
        tuple(params)
    )

    result = cursor.fetchone()

    cursor.close()

    conn.close()

    return result


# ------------------------------------------------------------
# GET PENDING PAYMENTS
# ------------------------------------------------------------

def get_pending_payments(branch_id=None):

    conn = get_connection()

    query = """
        SELECT
            cs.sale_id,
            b.branch_name,
            cs.date,
            cs.name,
            cs.mobile_number,
            cs.product_name,
            cs.gross_sales,
            cs.received_amount,
            cs.pending_amount,
            cs.status
        FROM customer_sales cs
        JOIN branches b
            ON cs.branch_id = b.branch_id
        WHERE cs.pending_amount > 0
    """

    params = []

    if branch_id is not None:

        query += """
            AND cs.branch_id = %s
        """

        params.append(branch_id)

    query += """
        ORDER BY cs.pending_amount DESC
    """

    df = pd.read_sql(
        query,
        conn,
        params=tuple(params)
    )

    conn.close()

    return df


# ------------------------------------------------------------
# GET PAYMENT METHOD SUMMARY
# ------------------------------------------------------------

def get_payment_method_summary(branch_id=None):

    conn = get_connection()

    query = """
        SELECT
            ps.payment_method,
            COALESCE(SUM(ps.amount_paid), 0) AS total_collection
        FROM payment_splits ps
        JOIN customer_sales cs
            ON ps.sale_id = cs.sale_id
    """

    params = []

    if branch_id is not None:

        query += """
            WHERE cs.branch_id = %s
        """

        params.append(branch_id)

    query += """
        GROUP BY ps.payment_method
        ORDER BY total_collection DESC
    """

    df = pd.read_sql(
        query,
        conn,
        params=tuple(params)
    )

    conn.close()

    return df


# ------------------------------------------------------------
# GET PAYMENT DETAILS
# ------------------------------------------------------------

def get_payment_details(branch_id=None):

    conn = get_connection()

    query = """
        SELECT
            ps.payment_id,
            ps.sale_id,
            b.branch_name,
            cs.name AS customer_name,
            ps.payment_date,
            ps.amount_paid,
            ps.payment_method
        FROM payment_splits ps
        JOIN customer_sales cs
            ON ps.sale_id = cs.sale_id
        JOIN branches b
            ON cs.branch_id = b.branch_id
        WHERE 1 = 1
    """

    params = []

    if branch_id is not None:

        query += """
            AND cs.branch_id = %s
        """

        params.append(branch_id)

    query += """
        ORDER BY ps.payment_date DESC, ps.payment_id DESC
    """

    df = pd.read_sql(
        query,
        conn,
        params=tuple(params)
    )

    conn.close()

    return df


# ------------------------------------------------------------
# GET SALES FOR PAYMENT
# ------------------------------------------------------------

def get_sales_for_payment(branch_id=None):

    conn = get_connection()

    query = """
        SELECT
            sale_id,
            name,
            product_name,
            gross_sales,
            received_amount,
            pending_amount,
            branch_id
        FROM customer_sales
        WHERE pending_amount > 0
    """

    params = []

    if branch_id is not None:

        query += """
            AND branch_id = %s
        """

        params.append(branch_id)

    query += """
        ORDER BY sale_id
    """

    df = pd.read_sql(
        query,
        conn,
        params=tuple(params)
    )

    conn.close()

    return df


# ------------------------------------------------------------
# ADD SALE
# ------------------------------------------------------------

def add_sale(
    branch_id,
    sale_date,
    name,
    mobile_number,
    product_name,
    gross_sales,
    status
):

    conn = get_connection()

    query = """
        INSERT INTO customer_sales
        (
            branch_id,
            date,
            name,
            mobile_number,
            product_name,
            gross_sales,
            received_amount,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            0,
            %s
        )
    """

    cursor = conn.cursor()

    cursor.execute(
        query,
        (
            branch_id,
            sale_date,
            name,
            mobile_number,
            product_name,
            gross_sales,
            status
        )
    )

    conn.commit()

    cursor.close()

    conn.close()


# ------------------------------------------------------------
# ADD PAYMENT SPLIT
# ------------------------------------------------------------

def add_payment(
    sale_id,
    payment_date,
    amount_paid,
    payment_method
):

    conn = get_connection()

    query = """
        INSERT INTO payment_splits
        (
            sale_id,
            payment_date,
            amount_paid,
            payment_method
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
    """

    cursor = conn.cursor()

    cursor.execute(
        query,
        (
            sale_id,
            payment_date,
            amount_paid,
            payment_method
        )
    )

    conn.commit()

    cursor.close()

    conn.close()


# ------------------------------------------------------------
# EXECUTE SQL QUERY
# ------------------------------------------------------------

def execute_query(query):

    conn = get_connection()

    df = pd.read_sql(
        query,
        conn
    )

    conn.close()

    return df


# ============================================================
# PREDEFINED SQL QUERIES
# ============================================================

SQL_QUERIES = {

    "Q1 - All Customer Sales": """
        SELECT *
        FROM customer_sales;
    """,

    "Q2 - All Branches": """
        SELECT *
        FROM branches;
    """,

    "Q3 - All Payment Splits": """
        SELECT *
        FROM payment_splits;
    """,

    "Q4 - Open Sales": """
        SELECT *
        FROM customer_sales
        WHERE status = 'Open';
    """,

    "Q5 - Chennai Sales": """
        SELECT
            cs.*
        FROM customer_sales cs
        JOIN branches b
            ON cs.branch_id = b.branch_id
        WHERE b.branch_name = 'Chennai';
    """,

    "Q6 - Total Gross Sales": """
        SELECT
            SUM(gross_sales) AS total_gross_sales
        FROM customer_sales;
    """,

    "Q7 - Total Received Amount": """
        SELECT
            SUM(received_amount) AS total_received_amount
        FROM customer_sales;
    """,

    "Q8 - Total Pending Amount": """
        SELECT
            SUM(pending_amount) AS total_pending_amount
        FROM customer_sales;
    """,

    "Q9 - Sales Count Per Branch": """
        SELECT
            b.branch_name,
            COUNT(cs.sale_id) AS total_sales
        FROM branches b
        LEFT JOIN customer_sales cs
            ON b.branch_id = cs.branch_id
        GROUP BY
            b.branch_id,
            b.branch_name
        ORDER BY total_sales DESC;
    """,

    "Q10 - Average Gross Sales": """
        SELECT
            AVG(gross_sales) AS average_gross_sales
        FROM customer_sales;
    """,

    "Q11 - Sales With Branch Name": """
        SELECT
            cs.sale_id,
            b.branch_name,
            cs.date,
            cs.name,
            cs.mobile_number,
            cs.product_name,
            cs.gross_sales,
            cs.received_amount,
            cs.pending_amount,
            cs.status
        FROM customer_sales cs
        JOIN branches b
            ON cs.branch_id = b.branch_id;
    """,

    "Q12 - Sales With Total Payment Received": """
        SELECT
            cs.sale_id,
            cs.name,
            cs.product_name,
            cs.gross_sales,
            COALESCE(
                SUM(ps.amount_paid),
                0
            ) AS total_payment_received
        FROM customer_sales cs
        LEFT JOIN payment_splits ps
            ON cs.sale_id = ps.sale_id
        GROUP BY
            cs.sale_id,
            cs.name,
            cs.product_name,
            cs.gross_sales;
    """,

    "Q13 - Branch Wise Gross Sales": """
        SELECT
            b.branch_name,
            SUM(cs.gross_sales) AS total_gross_sales
        FROM branches b
        JOIN customer_sales cs
            ON b.branch_id = cs.branch_id
        GROUP BY
            b.branch_id,
            b.branch_name
        ORDER BY total_gross_sales DESC;
    """,

    "Q14 - Sales With Payment Method": """
        SELECT
            cs.sale_id,
            cs.name,
            cs.product_name,
            ps.payment_method,
            ps.amount_paid
        FROM customer_sales cs
        JOIN payment_splits ps
            ON cs.sale_id = ps.sale_id;
    """,

    "Q15 - Sales With Branch Admin": """
        SELECT
            cs.sale_id,
            cs.name,
            cs.product_name,
            b.branch_name,
            b.branch_admin_name
        FROM customer_sales cs
        JOIN branches b
            ON cs.branch_id = b.branch_id;
    """,

    "Q16 - Pending Greater Than 5000": """
        SELECT
            sale_id,
            name,
            product_name,
            gross_sales,
            received_amount,
            pending_amount
        FROM customer_sales
        WHERE pending_amount > 5000
        ORDER BY pending_amount DESC;
    """,

    "Q17 - Top 3 Highest Gross Sales": """
        SELECT
            sale_id,
            name,
            product_name,
            gross_sales
        FROM customer_sales
        ORDER BY gross_sales DESC
        LIMIT 3;
    """,

    "Q18 - Branch With Highest Gross Sales": """
        SELECT
            b.branch_name,
            SUM(cs.gross_sales) AS total_gross_sales
        FROM branches b
        JOIN customer_sales cs
            ON b.branch_id = cs.branch_id
        GROUP BY
            b.branch_id,
            b.branch_name
        ORDER BY total_gross_sales DESC
        LIMIT 1;
    """,

    "Q19 - Monthly Sales Summary": """
        SELECT
            YEAR(date) AS year,
            MONTH(date) AS month,
            COUNT(*) AS total_sales,
            SUM(gross_sales) AS total_gross_sales,
            SUM(received_amount) AS total_received,
            SUM(pending_amount) AS total_pending
        FROM customer_sales
        GROUP BY
            YEAR(date),
            MONTH(date)
        ORDER BY
            year,
            month;
    """,

    "Q20 - Payment Method Collection": """
        SELECT
            payment_method,
            SUM(amount_paid) AS total_collection
        FROM payment_splits
        GROUP BY payment_method
        ORDER BY total_collection DESC;
    """
}


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if "user" not in st.session_state:

    st.session_state.user = None


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.title("📊 Sales Management System")

    st.subheader("Login")

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Login",
        use_container_width=True
    ):

        conn = get_connection()

        cursor = conn.cursor(
            dictionary=True
        )

        query = """
            SELECT
                user_id,
                username,
                password,
                branch_id,
                role,
                email
            FROM users
            WHERE username = %s
            AND password = %s
        """

        cursor.execute(
            query,
            (
                username,
                password
            )
        )

        user = cursor.fetchone()

        cursor.close()

        conn.close()

        if user:

            st.session_state.logged_in = True

            st.session_state.user = user

            st.rerun()

        else:

            st.error(
                "Invalid username or password."
            )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    user = st.session_state.user

    branches_df = get_branches()


    # ========================================================
    # SIDEBAR
    # ========================================================

    st.sidebar.title("👤 User Information")

    st.sidebar.write(
        f"**Username:** {user['username']}"
    )

    st.sidebar.write(
        f"**Role:** {user['role']}"
    )

    if user["branch_id"] is not None:

        branch_row = branches_df[
            branches_df["branch_id"]
            == user["branch_id"]
        ]

        if not branch_row.empty:

            branch_name = branch_row.iloc[0]["branch_name"]

            st.sidebar.write(
                f"**Branch:** {branch_name}"
            )

    else:

        st.sidebar.write(
            "**Branch:** All Branches"
        )

    st.sidebar.divider()


    # ========================================================
    # LOGOUT
    # ========================================================

    if st.sidebar.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.user = None

        st.rerun()


    # ========================================================
    # BRANCH FILTER
    # ========================================================

    if user["role"] == "Super Admin":

        branch_options = (
            ["All Branches"]
            + branches_df["branch_name"].tolist()
        )

        selected_branch = st.sidebar.selectbox(
            "Filter Branch",
            branch_options
        )

        if selected_branch == "All Branches":

            selected_branch_id = None

        else:

            selected_branch_id = int(
                branches_df.loc[
                    branches_df["branch_name"]
                    == selected_branch,
                    "branch_id"
                ].iloc[0]
            )

    else:

        selected_branch_id = user["branch_id"]


    # ========================================================
    # PAGE TITLE
    # ========================================================

    st.title("📊 Sales Management System")


    # ========================================================
    # DASHBOARD HEADER
    # ========================================================

    if user["role"] == "Super Admin":

        st.header(
            "Super Admin Dashboard"
        )

    else:

        branch_row = branches_df[
            branches_df["branch_id"]
            == user["branch_id"]
        ]

        branch_name = branch_row.iloc[0]["branch_name"]

        st.header(
            f"{branch_name} Branch Dashboard"
        )


    # ========================================================
    # KPI SUMMARY
    # ========================================================

    summary = get_sales_summary(
        selected_branch_id
    )

    total_sales = summary["total_sales"]

    total_gross_sales = summary[
        "total_gross_sales"
    ]

    total_received = summary[
        "total_received"
    ]

    total_pending = summary[
        "total_pending"
    ]

    if total_gross_sales > 0:

        pending_percentage = (
            total_pending
            / total_gross_sales
        ) * 100

    else:

        pending_percentage = 0


    st.subheader(
        "Financial Summary"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Total Sales",
        total_sales
    )

    col2.metric(
        "Gross Sales",
        f"₹{total_gross_sales:,.2f}"
    )

    col3.metric(
        "Received",
        f"₹{total_received:,.2f}"
    )

    col4.metric(
        "Pending",
        f"₹{total_pending:,.2f}"
    )

    col5.metric(
        "Pending %",
        f"{pending_percentage:.2f}%"
    )


    # ========================================================
    # TABS
    # ========================================================

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📋 Sales",
            "💰 Pending Payments",
            "➕ Add Sale",
            "💳 Add Payment",
            "📊 Reports",
            "🔎 SQL Queries"
        ]
    )


    # ========================================================
    # TAB 1 - SALES
    # ========================================================

    with tab1:

        st.subheader(
            "Sales Report"
        )

        status_filter = st.selectbox(
            "Filter by Status",
            [
                "All",
                "Open",
                "Close"
            ]
        )

        if status_filter == "All":

            sales_status = None

        else:

            sales_status = status_filter

        sales_df = get_sales(
            selected_branch_id,
            sales_status
        )

        st.dataframe(
            sales_df,
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # TAB 2 - PENDING PAYMENTS
    # ========================================================

    with tab2:

        st.subheader(
            "Pending Payments"
        )

        pending_df = get_pending_payments(
            selected_branch_id
        )

        if pending_df.empty:

            st.success(
                "No pending payments."
            )

        else:

            st.dataframe(
                pending_df,
                use_container_width=True,
                hide_index=True
            )


    # ========================================================
    # TAB 3 - ADD SALE
    # ========================================================

    with tab3:

        st.subheader(
            "Add New Sale"
        )

        if user["role"] == "Super Admin":

            branch_dict = dict(
                zip(
                    branches_df["branch_name"],
                    branches_df["branch_id"]
                )
            )

            selected_sale_branch = st.selectbox(
                "Branch",
                list(branch_dict.keys())
            )

            sale_branch_id = branch_dict[
                selected_sale_branch
            ]

        else:

            sale_branch_id = user["branch_id"]

            branch_row = branches_df[
                branches_df["branch_id"]
                == sale_branch_id
            ]

            selected_sale_branch = branch_row.iloc[
                0
            ]["branch_name"]

            st.info(
                f"Sale will be added to "
                f"{selected_sale_branch} branch."
            )


        sale_date = st.date_input(
            "Sale Date"
        )

        customer_name = st.text_input(
            "Customer Name"
        )

        mobile_number = st.text_input(
            "Mobile Number"
        )

        product_name = st.text_input(
            "Product Name"
        )

        gross_sales = st.number_input(
            "Gross Sales",
            min_value=0.0,
            step=100.0
        )

        sale_status = st.selectbox(
            "Status",
            [
                "Open",
                "Close"
            ]
        )

        if st.button(
            "Add Sale",
            use_container_width=True
        ):

            if customer_name.strip() == "":

                st.error(
                    "Please enter customer name."
                )

            elif mobile_number.strip() == "":

                st.error(
                    "Please enter mobile number."
                )

            elif product_name.strip() == "":

                st.error(
                    "Please enter product name."
                )

            elif gross_sales <= 0:

                st.error(
                    "Gross sales must be greater than 0."
                )

            else:

                try:

                    add_sale(
                        sale_branch_id,
                        sale_date,
                        customer_name,
                        mobile_number,
                        product_name,
                        gross_sales,
                        sale_status
                    )

                    st.success(
                        "Sale added successfully."
                    )

                except mysql.connector.Error as e:

                    st.error(
                        f"Database error: {e}"
                    )


    # ========================================================
    # TAB 4 - ADD PAYMENT
    # ========================================================

    with tab4:

        st.subheader(
            "Add Payment Split"
        )

        payment_sales_df = get_sales_for_payment(
            selected_branch_id
        )

        if payment_sales_df.empty:

            st.info(
                "No pending sales available "
                "for payment."
            )

        else:

            payment_sales_df["display"] = (
                payment_sales_df["sale_id"].astype(str)
                + " - "
                + payment_sales_df["name"]
                + " - "
                + payment_sales_df["product_name"]
                + " - Pending ₹"
                + payment_sales_df[
                    "pending_amount"
                ].round(2).astype(str)
            )

            selected_sale_display = st.selectbox(
                "Select Sale",
                payment_sales_df["display"].tolist()
            )

            selected_sale = payment_sales_df[
                payment_sales_df["display"]
                == selected_sale_display
            ].iloc[0]

            st.write(
                f"**Gross Sales:** "
                f"₹{selected_sale['gross_sales']:,.2f}"
            )

            st.write(
                f"**Already Received:** "
                f"₹{selected_sale['received_amount']:,.2f}"
            )

            st.write(
                f"**Pending:** "
                f"₹{selected_sale['pending_amount']:,.2f}"
            )

            payment_date = st.date_input(
                "Payment Date"
            )

            amount_paid = st.number_input(
                "Amount Paid",
                min_value=0.01,
                max_value=float(
                    selected_sale["pending_amount"]
                ),
                step=100.0
            )

            payment_method = st.selectbox(
                "Payment Method",
                [
                    "Cash",
                    "UPI",
                    "Card"
                ]
            )

            if st.button(
                "Add Payment",
                use_container_width=True
            ):

                try:

                    add_payment(
                        int(selected_sale["sale_id"]),
                        payment_date,
                        amount_paid,
                        payment_method
                    )

                    st.success(
                        "Payment added successfully."
                    )

                    st.info(
                        "The database trigger has "
                        "automatically updated the "
                        "received and pending amounts."
                    )

                except mysql.connector.Error as e:

                    st.error(
                        f"Database error: {e}"
                    )


    # ========================================================
    # TAB 5 - REPORTS
    # ========================================================

    with tab5:

        st.subheader(
            "Business Insights & Reports"
        )


        # ----------------------------------------------------
        # BRANCH PERFORMANCE
        # ----------------------------------------------------

        st.write(
            "### Branch-wise Sales Performance"
        )

        branch_report = get_sales(
            selected_branch_id
        )

        if not branch_report.empty:

            if selected_branch_id is None:

                branch_summary = (
                    branch_report
                    .groupby("branch_name")
                    .agg(
                        total_sales=(
                            "sale_id",
                            "count"
                        ),
                        gross_sales=(
                            "gross_sales",
                            "sum"
                        ),
                        received=(
                            "received_amount",
                            "sum"
                        ),
                        pending=(
                            "pending_amount",
                            "sum"
                        )
                    )
                    .reset_index()
                )

                st.dataframe(
                    branch_summary,
                    use_container_width=True,
                    hide_index=True
                )

                st.bar_chart(
                    branch_summary.set_index(
                        "branch_name"
                    )["gross_sales"]
                )

            else:

                st.info(
                    "Select 'All Branches' to "
                    "view branch comparison."
                )


        # ----------------------------------------------------
        # RECEIVED VS PENDING
        # ----------------------------------------------------

        st.write(
            "### Received vs Pending"
        )

        received_pending_df = pd.DataFrame(
            {
                "Amount": [
                    total_received,
                    total_pending
                ]
            },
            index=[
                "Received",
                "Pending"
            ]
        )

        st.bar_chart(
            received_pending_df
        )


        # ----------------------------------------------------
        # PAYMENT METHOD ANALYSIS
        # ----------------------------------------------------

        st.write(
            "### Payment Method Analysis"
        )

        payment_method_df = (
            get_payment_method_summary(
                selected_branch_id
            )
        )

        if payment_method_df.empty:

            st.info(
                "No payment data available."
            )

        else:

            st.dataframe(
                payment_method_df,
                use_container_width=True,
                hide_index=True
            )

            st.bar_chart(
                payment_method_df.set_index(
                    "payment_method"
                )["total_collection"]
            )


        # ----------------------------------------------------
        # SALES TREND
        # ----------------------------------------------------

        st.write(
            "### Monthly Sales Trend"
        )

        conn = get_connection()

        trend_query = """
            SELECT
                DATE_FORMAT(
                    date,
                    '%Y-%m'
                ) AS month,
                SUM(gross_sales) AS gross_sales
            FROM customer_sales
        """

        trend_params = []

        if selected_branch_id is not None:

            trend_query += """
                WHERE branch_id = %s
            """

            trend_params.append(
                selected_branch_id
            )

        trend_query += """
            GROUP BY
                DATE_FORMAT(
                    date,
                    '%Y-%m'
                )
            ORDER BY month
        """

        trend_df = pd.read_sql(
            trend_query,
            conn,
            params=tuple(trend_params)
        )

        conn.close()

        if not trend_df.empty:

            trend_df["month"] = pd.to_datetime(
                trend_df["month"]
            )

            trend_df = trend_df.set_index(
                "month"
            )

            st.line_chart(
                trend_df["gross_sales"]
            )


    # ========================================================
    # TAB 6 - SQL QUERIES
    # ========================================================

    with tab6:

        st.subheader(
            "Predefined SQL Queries"
        )

        selected_query_name = st.selectbox(
            "Select SQL Query",
            list(SQL_QUERIES.keys())
        )

        st.code(
            SQL_QUERIES[selected_query_name],
            language="sql"
        )

        if st.button(
            "Execute Query",
            use_container_width=True
        ):

            try:

                result_df = execute_query(
                    SQL_QUERIES[
                        selected_query_name
                    ]
                )

                st.success(
                    "Query executed successfully."
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )

            except Exception as e:

                st.error(
                    f"Query execution error: {e}"
                )


# ============================================================
# MAIN PROGRAM
# ============================================================

if st.session_state.logged_in:

    dashboard()

else:

    login_page()    