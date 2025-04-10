def load_css():
    """
    Returns custom CSS styling for the application
    """
    return """
    <style>
        /* Main layout styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        h1, h2, h3 {
            color: #2c3e50;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        h1 {
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            border-bottom: 1px solid #ddd;
            padding-bottom: 7px;
            margin-top: 30px;
        }
        
        /* Card styling */
        .stat-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card h1 {
            font-size: 2.5rem;
            color: #4e73df;
            margin-bottom: 0.5rem;
            border-bottom: none;
        }
        .stat-card p {
            color: #5a5c69;
            font-size: 1rem;
            margin-bottom: 0;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-size: 1rem;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #45a049;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        /* Form styling */
        div.row-widget.stRadio > div {
            flex-direction: row;
        }
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
        }
        
        /* Alert styling */
        .stAlert {
            border-radius: 5px;
        }
        
        /* Table styling */
        [data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        /* Login container */
        .login-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 30px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }
        
        /* Required field marker */
        .required:after {
            content: " *";
            color: red;
        }
    </style>
    """
