"""An example producer."""

import shutil

from robocorp import browser
from robocorp.tasks import task
from RPA.Archive import Archive
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Tables import Tables


@task
def order_robots_from_RobotSpareBin():
    """Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images."""
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    close_annoying_modal()
    table = get_orders()
    table = read_tables()
    loop_orders(table)
    archive_receipts()
    clean_up()


def open_robot_order_website():
    """navigate to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def close_annoying_modal():
    """closes modal"""
    page = browser.page()
    page.click("button:text('OK')")


def get_orders():
    """get orders from CSV file"""
    http = HTTP()
    table = http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    return table


def read_tables():
    tables = Tables()
    table = tables.read_table_from_csv("orders.csv")
    return table


def loop_orders(table):
    """loop all orders"""
    page = browser.page()
    for row in table:
        fill_order(row)
        pdf_file = store_receipt_as_pdf(row["Order number"])
        screenshot = screenshot_robot(row["Order number"])
        embed_screenshot_to_receipt(screenshot, pdf_file)
        page.click("#order-another")
        close_annoying_modal()


def fill_order(row):
    """make order"""
    page = browser.page()
    page.select_option("#head", row["Head"])
    selector = f"#id-body-{row['Body']}"
    page.set_checked(selector, True)
    page.fill("#address", row["Address"])

    element = page.get_by_placeholder("Enter the part number for the legs")
    element.fill(row["Legs"])

    page.click("button:text('Preview')")
    page.click("#preview")

    is_visible = True
    while is_visible:
        page.click("#order")
        element = page.locator("//div[@class='alert alert-danger']")
        is_visible = element.is_visible()
        if not is_visible:
            break


def store_receipt_as_pdf(order_number):
    """Export the data to a pdf file"""
    page = browser.page()
    sales_results_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf_file = "output/receipts/{0}.pdf".format(order_number)
    pdf.html_to_pdf(sales_results_html, pdf_file)
    return pdf_file


def screenshot_robot(order_number):
    page = browser.page()
    screenshot_path = "output/screenshot/{0}.png".format(order_number)
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path


def embed_screenshot_to_receipt(screenshot_path, pdf_file):
    """Embeds the screenshot to the bot receipt"""
    pdf = PDF()

    pdf.add_files_to_pdf(files=[screenshot_path], target_document=pdf_file, append=True)


def archive_receipts():
    """Create a Zip File of the Receipts"""
    lib = Archive()
    lib.archive_folder_with_zip("./output/receipts", "./output/receipts.zip")


def clean_up():
    """Cleans up the folders where receipts and screenshots are saved."""
    shutil.rmtree("./output/receipts")
    shutil.rmtree("./output/screenshot")
