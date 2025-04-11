import streamlit as st

def generate_product_page():
    st.title("Generate Product")

    # Layout with two columns: inputs on the left, preview on the right
    left_col, right_col = st.columns([1, 2])

    with left_col:
        # Input fields
        design_name = st.text_input("Design Name", placeholder="Value")
        marketplace_title = st.text_input("Marketplace Title (80 character limit)", placeholder="Value")
        design_sku = st.text_input("Design SKU", value="324234", disabled=True)

        # Multi-select for sizes and colors
        sizes = st.multiselect("Select Sizes", ["Small", "Medium", "Large", "XL", "2XL"])
        colors = st.multiselect("Select Colours", ["Black", "Navy", "Grey", "White", "Red"])

        # File uploader for design image
        design_image = st.file_uploader("Design Image", type=["png", "jpg", "jpeg"])

        # Generate button
        if st.button("Generate"):
            st.success("Product generated successfully!")

    with right_col:
        # Preview by color
        st.write("### Preview by Colour")
        col1, col2, col3 = st.columns(3)

        with col1:
            color1 = st.selectbox("Select Color 1", colors if colors else ["Black", "White", "Navy", "Grey"], key="color1")
            if design_image:
                st.image(design_image, width=100, caption=color1)
            else:
                st.image("https://via.placeholder.com/100", width=100, caption=color1)  # Placeholder image

        with col2:
            color2 = st.selectbox("Select Color 2", colors if colors else ["Black", "White", "Navy", "Grey"], key="color2")
            if design_image:
                st.image(design_image, width=100, caption=color2)
            else:
                st.image("https://via.placeholder.com/100", width=100, caption=color2)  # Placeholder image

        with col3:
            color3 = st.selectbox("Select Color 3", colors if colors else ["Black", "White", "Navy", "Grey"], key="color3")
            if design_image:
                st.image(design_image, width=100, caption=color3)
            else:
                st.image("https://via.placeholder.com/100", width=100, caption=color3)  # Placeholder image

# Call the function to render the page
generate_product_page()