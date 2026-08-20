def build_unilog_header():
    header = [
        "MFR URL",
        "Ref URL 1",
        "Ref URL 2",
        "Ref URL 3",
        "Ref URL 4",
        "Ref URL 5",
        "PART_NUMBER",
        "Dept",
        "Class",
        "Fine",
        "SKU - MY_PART_NUMBER",
        "Mfg_Part_Num",
        "Part_Desc",
        "E1_Brand",
        "Unilog_Brand",
        "DIB_Brand",
        "Part_Manuf",
        "MANUFACTURER_NAME",
        "BRAND_NAME",
        "TRADE_NAME",
        "MANUFACTURER_PART_NUMBER",
        "ALTERNATE_PART_NUMBER",
        "Classpath",
        "MOBILE_DESC",
        "INVOICE_DESC",
        "SHORT_DESC",
        "LONG_DESC1",
        "RETAIL_DESC",
        "MARKETING_DESCRIPTION",
    ]

    for i in range(1, 21):
        header.append(f"ITEM_FEATURES_{i}")

    header += [
        "With",
        "Standard/Approvals",
        "Prop 65",
        "Application",
        "Includes",
        "Product Name",
    ]

    for i in range(1, 51):
        header.append(f"ATTRIBUTE_LABEL {i}")
        header.append(f"ATTRIBUTE_VALUE {i}")
        header.append(f"ATTRIBUTE_UOM {i}")

    header += [
        "UPC",
        "EAN",
        "GTIN",
        "UNSPSC",
        "Warranty",
        "List Price",
        "Selling Qty",
        "Selling UOM",
        "Standard Packaging Information",
        "LENGTH",
        "LENGTH_UOM",
        "HEIGHT",
        "HEIGHT_UOM",
        "WIDTH",
        "WIDTH_UOM",
        "WEIGHT",
        "WEIGHT_UOM",
        "VOLUME",
        "VOLUME_UOM",
        "Product Image",
        "Alternate Image 1",
        "Alternate Image 2",
        "Alternate Image 3",
        "Alternate Image 4",
        "SDS",
        "SDS_1",
        "Warranty Information",
        "Catalog",
        "Specification Sheet",
        "Instruction/Installation Manual",
        "Service Manual",
        "Owners/User Manual",
        "Line Drawing",
        "MTR",
        "RoHS",
        "Full Engineering Drawing",
        "Energy Star Guide",
        "Technical Bulletin",
        "Submittal",
        "Compatibility Chart",
        "Size Chart",
        "Product Label/Insert",
        "Video Link",
        "Video Link 1",
        "Country Of Origin",
        "Discontinued",
        "Actual Image (Yes/No)",
    ]

    return header

UNILOG_HEADER = build_unilog_header()
