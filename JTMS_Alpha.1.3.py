import os
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp, sp
from kivy.uix.dropdown import DropDown
from kivy.base import runTouchApp
from datetime import datetime
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from functools import partial
import uuid
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line


# Set the window size to a common mobile resolution
Window.size = (360, 640)  # This is a downscaled resolution from 1080x1920 for practicality

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',  # Keep existing scope for Google Sheets
    'https://www.googleapis.com/auth/userinfo.email',  # Add scope for user's email address
    'https://www.googleapis.com/auth/userinfo.profile',  # Add scope for user profile information
    'https://www.googleapis.com/auth/drive.file',
    'openid',  # OpenID scope for signing the user in
]


# Google Sheet IDs and Range Names
USERS_SHEET_ID = '1IbhdQiK_Cv0NIS276svmB6rFJodrhlvcBCeP1p4m0Mc'
USERS_RANGE = 'Users!A:G'
CUSTOMERS_SHEET_ID = '1JyQ3MMb1WVUddC_kRsIrWvxExCzbOa_Bv5i6kig8DPI'
CUSTOMERS_RANGE = 'Customers!A:F'
TASK_REPORTS_SHEET_ID = '1NcNuragbIMj_pfk20rBOCSXyuUhCm2td9orc_p6kNZk'
TASK_REPORTS_RANGE = 'A:H'  # Assuming the name of the sheet is 'Task Reports'

def get_google_sheets_service():
    try:
        creds = None
        # Check if the token.json file exists
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If no valid credentials are found, log in and save the credentials
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('sheets', 'v4', credentials=creds)
        return service.spreadsheets()
    except Exception as e:
        print(f"Error setting up Google Sheets service: {e}")
        return None

def load_data_from_sheet(spreadsheet_id, range_name):
    service = get_google_sheets_service()
    if service:
        try:
            result = service.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            if not values:
                print("No data found.")
                return []
            headers = values[0]
            data = [dict(zip(headers, row)) for row in values[1:]]
            return data
        except HttpError as error:
            print(f"An error occurred: {error}")
    return []

def upload_file_to_drive(file_path, folder_id, report_id):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    service = build('drive', 'v3', credentials=creds)
    
    # Incorporate the report ID into the file name
    original_file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(original_file_name)[1]
    new_file_name = f"{report_id}{file_extension}"  
    
    file_metadata = {'name': new_file_name, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    
    print('File ID: %s' % file.get('id'))  # You can remove this print statement if not needed
    # Print the URL to the console
    print('File URL: %s' % file.get('webViewLink'))
    return file.get('webViewLink')  # Return the URL of the uploaded file

def fetch_file_url_by_report_id(report_id):
    service = get_google_sheets_service()  # Ensure you have a function to authenticate and get the service
    sheet_id = TASK_REPORTS_SHEET_ID
    range_name = 'G:G'  # Adjust based on your actual range

    # Fetch the data
    result = service.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])

    # Find the URL by ReportID, ensuring row length is sufficient
    print(f"Fetching URL for Report ID: {report_id}")
    file_url = next((row[6] for row in values if len(row) > 6 and row[0] == report_id), None)
    print(f"Fetched URL: {file_url}")
    return file_url


def list_files_in_folder(self, folder_id):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('drive', 'v3', credentials=creds)
    
    results = service.files().list(
        q="'{}' in parents".format(folder_id),
        pageSize=10, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(10),
                           size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Determine the size of the layout based on the screen size
        layout_width = dp(300)
        layout_height = dp(500)
        layout.size = (layout_width, layout_height)

        # Logo image at the top
        logo_path = "JTMS Logo.png"  # Ensure this is the correct path relative to the app
        logo_image = Image(source=logo_path, allow_stretch=True, size_hint_y=None, height=dp(200))  # Increase the height as needed
        layout.add_widget(logo_image)

        # Username field
        layout.add_widget(Label(text='Username:', size_hint_y=None, height=dp(30), font_size=sp(16)))
        self.username_input = TextInput(multiline=False, size_hint=(0.8, None), height=dp(40), font_size=sp(16), pos_hint={'center_x': 0.5})
        layout.add_widget(self.username_input)

        # Password field
        layout.add_widget(Label(text='Password:', size_hint_y=None, height=dp(30), font_size=sp(16)))
        self.password_input = TextInput(password=True, multiline=False, size_hint=(0.8, None), height=dp(40), font_size=sp(16), pos_hint={'center_x': 0.5})
        layout.add_widget(self.password_input)

        # Login button
        login_button = Button(text='Login', size_hint=(0.8, None), height=dp(50), font_size=sp(18), pos_hint={'center_x': 0.5})
        login_button.bind(on_press=self.on_login_pressed)
        layout.add_widget(login_button)

        # Login with Google button
        self.login_with_google_button = Button(text='Login with Google', size_hint=(0.8, None), height=dp(50), pos_hint={'center_x': 0.5})
        self.login_with_google_button.bind(on_press=self.on_login_with_google_pressed)
        layout.add_widget(self.login_with_google_button)

        self.add_widget(layout)

    def on_login_pressed(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        users = load_data_from_sheet(USERS_SHEET_ID, USERS_RANGE)
        user = self.authenticate(username, password, users)
        if user:
            App.get_running_app().user_info = user  # Store user info in the app instance
            # Direct users based on their role
            if user['Role'] == 'Chairman':
                self.manager.current = 'group_selection'
            elif user['Role'] == 'Member':
                self.manager.current = 'customer_list'
            elif user['Role'] == 'Observer':
                # Direct Observer to a specific screen, assuming it's 'observer_screen'
                # You may need to adjust the screen name based on your application's design
                self.manager.current = 'observer_screen'
            else:
                # Handle other roles or default case
                # Direct them to a generic or overview screen, if applicable
                self.manager.current = 'customer_list'  # Adjust as needed for other roles
        else:
            self.show_popup("Login Failed", "Invalid username or password.")


    def authenticate(self, username, password, users):
        for user in users:
            if user['Username'] == username and user['PasswordHash'] == password:
                return user
        return None
    
    def on_login_with_google_pressed(self, instance):
        try:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            creds = flow.run_local_server(port=8080)
            
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            
            if user_info and user_info.get('email'):
                users = load_data_from_sheet(USERS_SHEET_ID, USERS_RANGE)
                email = user_info.get('email')
                # Adapt the authentication logic to match based on email
                user = next((u for u in users if u.get('Email', '').strip().lower() == email.strip().lower()), None)
                
                if user:
                    App.get_running_app().user_info = user  # Store user info in the app instance
                    # Direct users based on their role, adapted from on_login_pressed
                    if user['Role'] == 'Chairman':
                        self.manager.current = 'group_selection'
                    elif user['Role'] == 'Member':
                        self.manager.current = 'customer_list'
                    elif user['Role'] == 'Admin':
                        self.manager.current = 'admin_dashboard'
                    elif user['Role'] == 'Leader':
                        self.manager.current = 'verify_report'  # Navigate leaders to the verify_report screen
                    elif user['Role'] == 'Observer':
                        # Assuming 'observer_screen' is the screen you want observers to see
                        # You may need to adjust the screen name based on your application's design
                        self.manager.current = 'observer_screen'
                    else:
                        self.show_popup("Login Failed", "User role not recognized.")
                else:
                    self.show_popup("Login Failed", "User email not found in the system.")
            else:
                self.show_popup("Login Failed", "Could not get user information from Google.")
        except Exception as e:
            self.show_popup("Login Failed", str(e))

    
    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()


class GroupSelectionScreen(Screen):
    def on_enter(self, *args):
        super(GroupSelectionScreen, self).on_enter(*args)
        self.layout = BoxLayout(orientation='vertical', padding=10)
        self.clear_widgets()
        self.add_widget(self.layout)
        
        groups = set()
        customers = load_data_from_sheet(CUSTOMERS_SHEET_ID, CUSTOMERS_RANGE)
        for customer in customers:
            groups.add(customer['AssignedGroup'])
        
        for group in groups:
            # Replace "Group: Group1" with "Sektor 1" and so on for each group
            display_name = group.replace("Group", "Sektor") if 'Group' in group else group
            group_btn = Button(text=display_name)
            group_btn.bind(on_press=lambda instance, g=group: self.view_reports(instance, g))
            self.layout.add_widget(group_btn)

        # Add Logout Button here
        logout_button = Button(text='Logout')
        logout_button.bind(on_press=self.on_logout_pressed)
        self.layout.add_widget(logout_button)

    def view_reports(self, instance, group):
        App.get_running_app().selected_group = group
        self.manager.current = 'report_summary'

    def on_logout_pressed(self, instance):
        self.manager.current = 'login'  # Change to login screen

class CustomerScreen(Screen):
    def on_enter(self, *args):
        super(CustomerScreen, self).on_enter(*args)
        self.clear_widgets()

        # Overall layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Welcome message at the top
        user = App.get_running_app().user_info
        layout.add_widget(Label(text=f"Welcome, {user['Username']}!", size_hint_y=None, height=dp(40)))

        # Scrollable list for customers or actions
        scroll_view = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height))
        customer_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        customer_layout.bind(minimum_height=customer_layout.setter('height'))

        # Fixed "Verify Pending Reports" button for 'Leader'
        if user['Role'] == 'Leader':
            # Define the button before the scroll view to make it fixed (non-scrollable)
            verify_reports_button = Button(text='Verify Pending Reports', size_hint_y=None, height=dp(40))
            verify_reports_button.bind(on_press=self.navigate_to_verify_report_screen)
            layout.add_widget(verify_reports_button)

            # Get the members in the same group as the leader
            group_members = self.get_group_members(user)
            # Display member tasks summary
            self.display_members_task_summary(customer_layout, group_members)

        # Add user-specific content to the scrollable layout
        if user['Role'] in ['Chairman', 'Admin']:
            self.display_all_customers(customer_layout)
        elif user['Role'] == 'Member':
            self.display_member_specific_content(customer_layout, user)
        elif user['Role'] == 'Leader':
            # In case there are other things to display for the leader in the scroll view
            pass
        else:
            customer_layout.add_widget(Label(text="Your role does not have specific content.", size_hint_y=None, height=dp(40)))

        scroll_view.add_widget(customer_layout)
        layout.add_widget(scroll_view)

        # Logout button at the bottom
        logout_button = Button(text='Logout', size_hint=(1, None), height=dp(40))
        logout_button.bind(on_press=self.on_logout_pressed)
        layout.add_widget(logout_button)

        # Add the overall layout to the screen
        self.add_widget(layout)
    
    def get_group_members(self, leader):
        all_users = load_data_from_sheet(USERS_SHEET_ID, USERS_RANGE)
        leader_group = leader.get('AssignedGroup')  # Safely get the leader's AssignedGroup
        if not leader_group:  # If leader does not have an AssignedGroup, return an empty list
            return []
        group_members = [
            user for user in all_users 
            if user.get('AssignedGroup') == leader_group and user.get('Role') == 'Member'
        ]
        return group_members
    
    def get_member_task_info(self, member_username):
        all_tasks = load_data_from_sheet(TASK_REPORTS_SHEET_ID, TASK_REPORTS_RANGE)
        member_tasks = [task for task in all_tasks if task['UserName'] == member_username]
        verified_tasks = [task for task in member_tasks if task['TaskStatus'].lower() == 'verified']
        pending_tasks = [task for task in member_tasks if task['TaskStatus'].lower() == 'pending']
        return {
            'total': len(member_tasks),
            'verified': len(verified_tasks),
            'pending': len(pending_tasks)
        }
    
    def display_members_task_summary(self, layout, group_members):
        for member in group_members:
            task_info = self.get_member_task_info(member['Username'])
            member_info = f"{member['Username']}: Total Tasks: {task_info['total']}, Verified: {task_info['verified']}, Pending: {task_info['pending']}"
            layout.add_widget(Label(text=member_info, size_hint_y=None, height=dp(40)))


    def navigate_to_verify_report_screen(self, instance):
        self.manager.current = 'verify_report'

    def filter_customers_by_user(self, customers, user):
        if user['Role'] in ['Admin', 'Chairman']:
            return customers
        elif user['Role'] == 'Leader':
            assigned_group = user.get('AssignedGroup', '')
            pending_customer_ids = self.get_pending_report_customer_ids_for_leader(user['Username'])
            return [customer for customer in customers if customer.get('AssignedGroup') == assigned_group or str(customer.get('CustomerID')).strip() in pending_customer_ids]
        elif user['Role'] == 'Member':
            assigned_customer_ids = user.get('AssignedCustomers', '').split(',')
            assigned_customer_ids = [id.strip() for id in assigned_customer_ids]
            return [customer for customer in customers if str(customer.get('CustomerID')).strip() in assigned_customer_ids]
        return []

    def display_all_customers(self, layout):
        customers = load_data_from_sheet(CUSTOMERS_SHEET_ID, CUSTOMERS_RANGE)
        for customer in customers:
            btn = Button(text=customer['Name'], size_hint_y=None, height=dp(40))  # Fixed height for the button
            btn.bind(on_press=lambda instance, c=customer: self.show_customer_detail(c))
            layout.add_widget(btn)

    def get_pending_report_customer_ids_for_leader(self, leader_username):
        service = get_google_sheets_service()
        try:
            result = service.values().get(spreadsheetId=TASK_REPORTS_SHEET_ID, range=TASK_REPORTS_RANGE).execute()
            values = result.get('values', [])
            pending_reports = [row for row in values if row[5] == 'Pending' and row[1] == leader_username]
            pending_customer_ids = list(set(row[6] for row in pending_reports))  # Adjust as per your data structure
            return pending_customer_ids
        except Exception as e:
            print(f"Failed to fetch pending report customer IDs: {e}")
            return []

    def display_member_specific_content(self, layout, user):
        assigned_customer_ids = user.get('AssignedCustomers', '').split(',')
        customers = load_data_from_sheet(CUSTOMERS_SHEET_ID, CUSTOMERS_RANGE)
        for customer_id in assigned_customer_ids:
            customer = next((c for c in customers if str(c.get('CustomerID')).strip() == customer_id), None)
            if customer:
                btn = Button(text=customer['Name'], size_hint_y=None, height=dp(40))  # Fixed height for the button
                btn.bind(on_press=lambda instance, c=customer: self.show_customer_detail(c))
                layout.add_widget(btn)

    def show_customer_detail(self, customer):
        detail_screen = self.manager.get_screen('customer_detail')
        detail_screen.display_customer_details(customer, App.get_running_app().user_info.get('Role', ''))
        self.manager.transition.direction = 'left'
        self.manager.current = 'customer_detail'

    def on_logout_pressed(self, instance):
        self.manager.current = 'login'

class CustomerDetailScreen(Screen):
    selected_customer = None

    def __init__(self, **kwargs):
        super(CustomerDetailScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)
    
    def display_customer_details(self, customer, user_role):
        self.selected_customer = customer
        self.layout.clear_widgets()

        # Define fields to exclude from direct display, including WhatsAppNumber
        excluded_fields = ['CustomerID', 'AssignedGroup', 'WhatsAppNumber']
        for key, value in customer.items():
            if key not in excluded_fields:
                # Add a label for each customer detail except for the excluded fields
                self.layout.add_widget(Label(text=f"{key}: {value}"))

        # If a WhatsApp number exists, add a "Chat on WhatsApp" button
        if 'WhatsAppNumber' in customer and customer['WhatsAppNumber']:
            whatsapp_button = Button(text="Chat on WhatsApp")
            whatsapp_button.bind(on_press=lambda instance: self.open_whatsapp_chat(customer['WhatsAppNumber']))
            self.layout.add_widget(whatsapp_button)

        # Assume user_role is available. Include Report Task button if the user is a 'Member'
        if user_role == 'Member':
            report_task_button = Button(text="Report Task")
            report_task_button.bind(on_press=self.report_task)
            self.layout.add_widget(report_task_button)

        # Back button to return to the customer list
        back_button = Button(text='Back')
        back_button.bind(on_press=self.go_back)
        self.layout.add_widget(back_button)
    
    def open_whatsapp_chat(self, whatsapp_link):
        webbrowser.open(whatsapp_link)

    def go_back(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'customer_list'

    def report_task(self, instance):
        # Navigate to the TaskReportScreen with pre-populated customer info
        task_report_screen = self.manager.get_screen('task_report')
        task_report_screen.selected_customer = self.selected_customer
        task_report_screen.pre_populate_customer_info(self.selected_customer['Name'])
        self.manager.current = 'task_report'

def append_task_report(user_name, customer_name, task_type, report_time, report_id, file_url, notes):
    service = get_google_sheets_service()
    if service:
        # Include the notes in the values
        body = {
            'values': [[report_id, user_name, customer_name, task_type, report_time, 'Pending', file_url, notes]]
        }
        try:
            result = service.values().append(
                spreadsheetId=TASK_REPORTS_SHEET_ID,
                range=TASK_REPORTS_RANGE,
                valueInputOption='USER_ENTERED',
                body=body,
                insertDataOption='INSERT_ROWS'
            ).execute()
            print(f"Task report added successfully with file URL. {result.get('updates').get('updatedRows')} rows updated.")
        except Exception as e:
            print(f"Failed to append task report: {e}")

from kivy.logger import Logger

class TaskReportScreen(Screen):
    selected_customer = None
    selected_task_type = None  # To store the selected task type
    document_uploaded = False  # Flag to check if the document has been uploaded
    max_note_length = 200  # Set the maximum length of notes allowed

    def __init__(self, **kwargs):
        super(TaskReportScreen, self).__init__(**kwargs)
        self.report_id = str(uuid.uuid4())
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)

        self._setup_ui()

    def _setup_ui(self):
        # Customer ID TextInput
        self.customer_id_input = TextInput(hint_text='Customer ID', multiline=False, readonly=True)
        self.layout.add_widget(self.customer_id_input)

        # Notes TextInput
        self.notes_input = TextInput(
            hint_text='Enter notes here (max 200 characters)', 
            multiline=True, 
            size_hint=(1, None), 
            height=dp(100), 
            input_filter=self.input_filter_notes
        )
        self.layout.add_widget(self.notes_input)

        # Upload Document Button
        self.upload_doc_button = Button(text="Upload Document")
        self.upload_doc_button.bind(on_press=self.show_upload_dialog)
        self.layout.add_widget(self.upload_doc_button)

        # Task Type ToggleButtons
        self.task_type_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=120)
        self.task_type_buttons = []
        for task_type in ['Chat', 'Vidcall', 'Visit']:
            btn = ToggleButton(text=task_type, group='task_type', disabled=True)  # Initially disabled
            btn.bind(on_press=self.on_task_type_selected)
            self.task_type_layout.add_widget(btn)
            self.task_type_buttons.append(btn)
        self.layout.add_widget(self.task_type_layout)

        # Submit Task Report Button
        self.submit_button = Button(text='Submit Task Report', disabled=True)
        self.submit_button.bind(on_press=self.submit_task_report)
        self.layout.add_widget(self.submit_button)

        # Back Button
        self.back_button = Button(text='Back')
        self.back_button.bind(on_press=self.go_back)
        self.layout.add_widget(self.back_button)

    def on_notes_text(self, instance, value):
        # Update the character count label
        self.char_count_label.text = f'{len(value)}/{self.max_note_length}'

        # If the text length exceeds the max, trim it
        if len(value) > self.max_note_length:
            instance.text = value[:self.max_note_length]
            instance.do_cursor_movement('cursor_end')  # Move cursor to the end

    def on_task_type_selected(self, instance):
        self.selected_task_type = instance.text if instance.state == 'down' else None

    def input_filter_notes(self, text, from_undo):
        # Limit notes to self.max_note_length characters
        return text[:self.max_note_length - len(self.notes_input.text)]

    def submit_task_report(self, instance):
        if self.document_uploaded and self.selected_task_type:
            user_name = App.get_running_app().user_info['Username']
            customer_name = self.customer_id_input.text
            task_type = self.selected_task_type
            report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            notes = self.notes_input.text  # Retrieve the notes from the TextInput

            # Ensure you've obtained the file_url from the document upload process
            file_url = App.get_running_app().report_url_mapping.get(self.report_id, '')

            # Call append_task_report with the notes included
            append_task_report(user_name, customer_name, task_type, report_time, self.report_id, file_url, notes)

            # Clear the notes input field after successfully submitting the report
            self.notes_input.text = ""

            # Navigate to the success screen
            self.manager.current = 'some_success_screen'
            print("Task report submitted successfully.")
        else:
            if not self.document_uploaded:
                print("Please upload a document first.")
            if not self.selected_task_type:
                print("Please select a task type.")

    def on_enter(self, *args):
        super(TaskReportScreen, self).on_enter(*args)
        # Reset the report_id and UI state each time the screen is entered
        self.report_id = str(uuid.uuid4())
        self.document_uploaded = False
        self.submit_button.disabled = True
        # Resetting task type buttons to be disabled until a document is uploaded
        for btn in self.task_type_buttons:
            btn.state = 'normal'
            btn.disabled = True

    def pre_populate_customer_info(self, customer_name):
        # Clear the notes from the previous customer before populating new customer details
        self.notes_input.text = ""
        
        # Continue with populating the details for the new customer
        self.customer_id_input.text = customer_name
        # Any other necessary steps for pre-populating information for the new customer

    # Get notes and ensure they are within the limit
        notes = self.notes_input.text
        if len(notes) > self.max_note_length:
            # Display an error if notes exceed the limit
            self.show_popup('Error', 'Note length exceeds the maximum allowed.')
            return

    def show_upload_dialog(self, instance):
        # Create the layout
        box = BoxLayout(orientation='vertical')

        # Instantiate the Image widget for previews
        self.image_preview = Image(size_hint_y=0.3)
        box.add_widget(self.image_preview)

        # Instantiate the FileChooserListView
        self.file_chooser = FileChooserListView(filters=["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"], size_hint_y=0.5)

        # Bind the selection to the preview without partial as it's unnecessary here
        self.file_chooser.bind(on_selection=self.selected)

        # Add the FileChooser to the layout
        box.add_widget(self.file_chooser)

        # Create the Upload button
        self.upload_button = Button(text="Upload", size_hint_y=None, height=dp(50))
        self.upload_button.bind(on_press=self.perform_upload)

        # Create the Cancel button
        self.cancel_button = Button(text="Cancel", size_hint_y=None, height=dp(50))
        self.cancel_button.bind(on_press=self.dismiss_popup)

        # Add the buttons to a separate layout
        button_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        button_box.add_widget(self.upload_button)
        button_box.add_widget(self.cancel_button)

        # Add the button layout to the box
        box.add_widget(button_box)

        # Create and open the popup
        self.popup = Popup(title="Upload file", content=box, size_hint=(0.9, 0.9))
        self.popup.open()

    def selected(self, filechooser, selection):
        print("File selected:", selection)


    def perform_upload(self, instance):
        selection = self.file_chooser.selection
        if selection:
            self.upload_document(self.file_chooser, selection, None)
        else:
            print("No file selected.")

    def dismiss_popup(self, instance):
        self.popup.dismiss()

    def upload_document(self, chooser, selection, touch):
        if selection:
            file_path = selection[0]
            folder_id = '1KQerv5D1EaePUirMVBNp_GQg5hn6AZc1'  # Ensure this is your actual folder ID
            report_id = self.report_id  # The report ID for the current task

            # Upload the file to Google Drive
            file_url = upload_file_to_drive(file_path, folder_id, report_id)

            if file_url:
                # Assuming the MyApp class has the report_url_mapping attribute
                App.get_running_app().report_url_mapping[report_id] = file_url
                
                self.popup.dismiss()
                print("File uploaded successfully. URL updated in the sheet.")
                self.document_uploaded = True
                self.submit_button.disabled = False  # Enable the submit button after upload
                self.enable_task_type_buttons()
            else:
                print("File upload failed or URL not obtained.")
        else:
            print("No file selected.")

    def enable_task_type_buttons(self):
        for btn in self.task_type_buttons:
            btn.disabled = False  # Enable the task type buttons after upload

    def go_back(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'customer_detail'
        
class SuccessScreen(Screen):
    def __init__(self, **kwargs):
        super(SuccessScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        success_message = Label(text="Task report submitted successfully!")
        back_button = Button(text="Back to Home")

        # Bind the button press to a method that changes the screen
        back_button.bind(on_press=self.go_back_to_home)

        layout.add_widget(success_message)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def go_back_to_home(self, instance):
        # Change the current screen to 'customer_list' or your designated home screen
        self.manager.current = 'customer_list'

def update_task_report_status(report_id, new_status):
    service = get_google_sheets_service()
    if service:
        try:
            # Correctly specifying the sheet name as "Tasks"
            id_range = "A:A"  # Use the correct sheet name here
            result = service.values().get(spreadsheetId=TASK_REPORTS_SHEET_ID, range=id_range).execute()
            ids = result.get('values', [])

            row_to_update = None
            for index, value in enumerate(ids):
                if value and value[0] == report_id:
                    row_to_update = index + 1  # +1 because Sheets is 1-indexed
                    break

            if row_to_update:
                # Now correctly target the 'F' column in the 'Tasks' sheet
                update_range = f"F{row_to_update}"  # Correctly adjusted for 'Tasks' sheet
                body = {'values': [[new_status]]}
                service.values().update(
                    spreadsheetId=TASK_REPORTS_SHEET_ID,
                    range=update_range,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                print(f"Task report {report_id} status updated to {new_status}.")
            else:
                print(f"No matching report ID found for {report_id}.")
        except Exception as e:
            print(f"Failed to update task report status: {e}")

class VerifyReportScreen(Screen):
    def on_enter(self, *args):
        super(VerifyReportScreen, self).on_enter(*args)
        self.display_pending_reports()

    def view_notes(self, report, *args):
        popup_width = Window.width * 0.8  # 80% of the window width
        popup_height = Window.height * 0.4  # 40% of the window height

        # Assuming notes_label is the Label that contains the notes text
        notes_label = Label(
            text=report['Notes'], 
            size_hint_y=None, 
            size_hint_x=None, 
            width=popup_width - dp(40),  # Subtract some dp for padding
            halign='left', 
            valign='top',  # Align text to the top
            text_size=(popup_width - dp(40), None),  # Use the adjusted width for text_size width
        )

        # Bind texture_size to allow the label to grow vertically
        notes_label.bind(texture_size=notes_label.setter('size'))

        # Create the content BoxLayout with reduced padding
        content = BoxLayout(orientation='vertical', padding=[dp(10), dp(0), dp(10), dp(10)])  # Top, Right, Bottom, Left padding
        content.add_widget(notes_label)

        # Popup widget
        popup = Popup(
            title='Notes',
            content=content,
            size_hint=(None, None),  # Use absolute size instead of a hint
            size=(popup_width, popup_height),  # Use the popup size defined earlier
            auto_dismiss=True
        )

        # Open the Popup
        popup.open()

    def open_url(self, url, *args):
        webbrowser.open(url)
    
    def get_pending_reports(self):
        service = get_google_sheets_service()
        if service:
            try:
                # Assuming TASK_REPORTS_SHEET_ID and TASK_REPORTS_RANGE are defined and point to your Google Sheet's data
                result = service.values().get(spreadsheetId=TASK_REPORTS_SHEET_ID, range=TASK_REPORTS_RANGE).execute()
                values = result.get('values', [])
                
                # Assuming the first row contains headers and the sixth column contains the report status
                headers = values[0]
                # Change from row[-1] to row[5] as 'TaskStatus' is now in the sixth column
                reports = [dict(zip(headers, row)) for row in values[1:] if row[5].lower() == 'pending']
                
                return reports
            except Exception as e:
                print(f"Failed to fetch pending reports: {e}")
                return []
        else:
            return []

    def display_pending_reports(self):
        self.clear_widgets()

        # Create a ScrollView
        scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))

        # Create a GridLayout for content
        grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        customers = load_data_from_sheet(CUSTOMERS_SHEET_ID, CUSTOMERS_RANGE)
        customer_name_to_group = {customer['Name']: customer['AssignedGroup'] for customer in customers}
        leader_assigned_group = App.get_running_app().user_info.get('AssignedGroup', None)
        pending_reports = self.get_pending_reports()

        if leader_assigned_group:
            pending_reports = [
                report for report in pending_reports
                if customer_name_to_group.get(report['CustomerName'], 'Unknown') == leader_assigned_group
            ]

        if not pending_reports:
            grid_layout.add_widget(Label(text='No pending reports.', size_hint_y=None, height=dp(40)))
            # Add the back button here because there are no pending reports
            back_button = Button(text='Back', size_hint=(1, None), height=dp(50))
            back_button.bind(on_press=self.go_back)
            grid_layout.add_widget(back_button)
        else:
            for report in pending_reports:
                # Vertical layout for each report block
                report_block_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
                report_block_layout.bind(minimum_height=report_block_layout.setter('height'))

                # Line 1: Username - Customer Name
                line1_label = Label(text=f"{report['UserName']} - {report['CustomerName']}", size_hint_y=None, height=dp(30))
                report_block_layout.add_widget(line1_label)

                # Line 2: Task Type - Report Time
                line2_label = Label(text=f"{report['TaskType']} - {report['ReportTime']}", size_hint_y=None, height=dp(30))
                report_block_layout.add_widget(line2_label)

                # Line 3: Buttons
                line3_layout = GridLayout(cols=3, size_hint_y=None, height=dp(40))
                
                # "View Notes" button with callback
                view_notes_btn = Button(text="View Notes")
                view_notes_btn.bind(on_press=lambda instance, r=report: self.view_notes(r))
                
                # "View File" button with callback
                view_file_btn = Button(text="View File")
                view_file_btn.bind(on_press=lambda instance, r=report: self.open_url(r['FileURL']))

                # "Verify" button with callback
                verify_btn = Button(text="Verify")
                verify_btn.bind(on_press=lambda instance, r=report: self.verify_report(r))

                line3_layout.add_widget(view_notes_btn)
                line3_layout.add_widget(view_file_btn)
                line3_layout.add_widget(verify_btn)


                # Add the layouts to the report block
                report_block_layout.add_widget(line3_layout)

                # Add the report block to the main layout
                grid_layout.add_widget(report_block_layout)

        # Adding ScrollView and GridLayout to the screen
        scroll_view.add_widget(grid_layout)
        self.add_widget(scroll_view)

        if pending_reports:
            self.add_float_layout_with_back_button()

    def add_float_layout_with_back_button(self):
        # Create a FloatLayout for the Back button, positioned at the bottom of the screen
        float_layout = FloatLayout(size_hint=(1, None), height=dp(50))
        back_button = Button(text='Back', size_hint=(None, None), size=(Window.width, dp(50)), pos_hint={'x': 0, 'y': 0})
        back_button.bind(on_press=self.go_back)
        float_layout.add_widget(back_button)  # Add the Back button to the FloatLayout
        self.add_widget(float_layout)

    def open_url(self, url, *args):
        webbrowser.open(url)

    def verify_report(self, report):
        report_id = report['ReportID']
        new_status = 'Verified'
        update_task_report_status(report_id, new_status)
        # Refresh the reports display
        self.display_pending_reports()

    def go_back(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'customer_list'

def get_reports_for_group(selected_group):
    # Fetch all customers and map them to their groups
    customers_data = load_data_from_sheet(CUSTOMERS_SHEET_ID, 'A:F')
    customer_to_group = {customer['Name']: customer['AssignedGroup'] for customer in customers_data}
    
    # Fetch all task reports
    reports_data = load_data_from_sheet(TASK_REPORTS_SHEET_ID, 'A:F')
    
    # Filter reports by selected group
    filtered_reports = []
    for report in reports_data:
        customer_name = report['CustomerName']
        if customer_to_group.get(customer_name) == selected_group:
            filtered_reports.append(report)
    
    return filtered_reports

class StripedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind size and position to update canvas
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background for contrast
            self.rect = Rectangle(pos=self.pos, size=self.size)

class BorderedLabel(Label):
    def __init__(self, bg_color=(1, 1, 1, 1), **kwargs):
        super(BorderedLabel, self).__init__(**kwargs)
        self.bg_color = bg_color
        self.bind(size=self.update_canvas, pos=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)  # Use the provided background color
            Rectangle(pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)  # Border color
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

class ReportSummaryScreen(Screen):
    def on_enter(self, *args):
        super(ReportSummaryScreen, self).on_enter(*args)
        selected_group = App.get_running_app().selected_group
        self.display_reports_for_group(selected_group)

    def display_reports_for_group(self, group):
        self.clear_widgets()

        # Fetch and display reports for the selected group
        reports = get_reports_for_group(group)
        task_summary = self.get_task_summary(reports)

        # Main layout to hold everything
        main_layout = BoxLayout(orientation='vertical')

        # Label for the selected group name
        # Removed the colon for Sektor
        group_name_label = Label(text=f"Sektor {group}", size_hint_y=None, height=dp(40))
        main_layout.add_widget(group_name_label)

        # Display task summary information
        for task_type, counts in task_summary.items():
            task_summary_label = Label(text=f"{task_type}: Total: {counts['total']}, Pending: {counts['pending']}, Verified: {counts['verified']}", size_hint_y=None, height=dp(40))
            main_layout.add_widget(task_summary_label)

        # Header layout with an additional column for Username
        header_layout = GridLayout(cols=4, size_hint_y=None, height=dp(40))
        header_colors = (0.5, 0.5, 0.5, 1)
        for header_text in ["Sintua", "Jemaat", "Task", "Status"]:
            header_layout.add_widget(BorderedLabel(text=header_text, size_hint_y=None, height=dp(40), bg_color=header_colors, size_hint_x=None, width=Window.width / 4))

        main_layout.add_widget(header_layout)

        # Scrollable layout for reports
        scroll_layout = GridLayout(cols=4, size_hint=(None, None), spacing=10)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        scroll_layout.width = Window.width
        scroll_view = ScrollView(size_hint=(1, 0.8), do_scroll_x=False, do_scroll_y=True)
        scroll_view.add_widget(scroll_layout)

        main_layout.add_widget(scroll_view)

        if not reports:
            scroll_layout.add_widget(Label(text="No reports found for this group.", size_hint_y=None, height=dp(40), size_hint_x=None, width=Window.width))
        else:
            scroll_layout.height = len(reports) * dp(40)
            for report in reports:
                for value in [report['UserName'], report['CustomerName'], report['TaskType'], report['TaskStatus']]:
                    scroll_layout.add_widget(Label(text=str(value), size_hint_y=None, height=dp(40), size_hint_x=None, width=Window.width / 4))

        # Back button
        back_button_layout = BoxLayout(size_hint_y=None, height=dp(40))
        back_button = Button(text='Back')
        back_button.bind(on_press=self.go_to_group_selection)
        back_button_layout.add_widget(back_button)
        main_layout.add_widget(back_button_layout)

        self.add_widget(main_layout)

    def go_to_group_selection(self, instance):
        self.manager.current = 'group_selection'

    def get_task_summary(self, reports):
        summary = {}
        for report in reports:
            task_type = report['TaskType']
            if task_type not in summary:
                summary[task_type] = {'total': 0, 'pending': 0, 'verified': 0}
            summary[task_type]['total'] += 1
            if report['TaskStatus'].lower() == 'pending':
                summary[task_type]['pending'] += 1
            elif report['TaskStatus'].lower() == 'verified':
                summary[task_type]['verified'] += 1
        return summary

class ObserverReportSummaryScreen(Screen):
    def on_enter(self, *args):
        super(ObserverReportSummaryScreen, self).on_enter(*args)
        self.display_reports()

    def display_reports(self):
        self.clear_widgets()

        # Layout for content and back button
        main_layout = BoxLayout(orientation='vertical', spacing=10)

        # ScrollView for reports
        scroll_view = ScrollView(size_hint=(1, 0.9), size=(Window.width, Window.height))
        grid_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid_layout.bind(minimum_height=grid_layout.setter('height'))

        reports = self.get_all_reports()

        for report in reports:
            report_block_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
            report_block_layout.bind(minimum_height=report_block_layout.setter('height'))

            line1 = f"{report['UserName']} - {report['CustomerName']}"
            report_block_layout.add_widget(Label(text=line1, size_hint_y=None, height=dp(30)))

            line2 = f"{report['TaskType']} - {report['ReportTime']}"
            report_block_layout.add_widget(Label(text=line2, size_hint_y=None, height=dp(30)))

            button_layout = GridLayout(cols=2, size_hint_y=None, height=dp(40))
            view_notes_btn = Button(text="View Notes")
            view_file_btn = Button(text="View File")

            # Bind buttons to actions
            view_notes_btn.bind(on_press=lambda instance, r=report: self.view_notes(r))
            view_file_btn.bind(on_press=lambda instance, url=report['FileURL']: self.open_url(url))


            button_layout.add_widget(view_notes_btn)
            button_layout.add_widget(view_file_btn)

            report_block_layout.add_widget(button_layout)
            grid_layout.add_widget(report_block_layout)

        scroll_view.add_widget(grid_layout)
        main_layout.add_widget(scroll_view)

        def open_url(self, url, *args):
        # Open URL without trying to access a dictionary
            webbrowser.open(url)

        # Back button
        back_button = Button(text='Back', size_hint_y=None, height=dp(50))
        back_button.bind(on_press=lambda instance: self.go_back())
        main_layout.add_widget(back_button)

        self.add_widget(main_layout)

    def view_notes(self, report, *args):
        popup_width = Window.width * 0.8
        popup_height = Window.height * 0.6  # Increased height for better visibility
        notes_label = Label(text=report['Notes'], size_hint_y=None, width=popup_width - dp(40),
                            halign='left', valign='top', text_size=(popup_width - dp(40), None))
        notes_label.bind(texture_size=notes_label.setter('size'))

        content = BoxLayout(orientation='vertical', padding=[dp(20), dp(20), dp(20), dp(20)])
        content.add_widget(notes_label)

        popup = Popup(title="Notes", content=content, size_hint=(None, None), size=(popup_width, popup_height))
        popup.open()

    def open_url(self, url, *args):
        webbrowser.open(url)

    def go_back(self):
        self.manager.transition.direction = 'left'
        # Assuming 'login' is the screen to go back to, adjust if necessary
        self.manager.current = 'login'  # Adjust to the correct screen to go back to

    def get_all_reports(self):
        service = get_google_sheets_service()
        if service:
            try:
                result = service.values().get(spreadsheetId=TASK_REPORTS_SHEET_ID, range=TASK_REPORTS_RANGE).execute()
                values = result.get('values', [])

                if not values:
                    print("No data found.")
                    return []

                headers = values[0]
                return [dict(zip(headers, row)) for row in values[1:]]
            except Exception as e:
                print(f"Failed to fetch reports: {e}")
                return []
        else:
            return []

class MyApp(App):
    user_info = {}  # Existing
    report_url_mapping = {}  # Add this line to initialize the mapping
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(CustomerScreen(name='customer_list'))
        sm.add_widget(CustomerDetailScreen(name='customer_detail'))
        sm.add_widget(TaskReportScreen(name='task_report'))
        sm.add_widget(SuccessScreen(name='some_success_screen'))
        sm.add_widget(VerifyReportScreen(name='verify_report'))
        sm.add_widget(ReportSummaryScreen(name='report_summary'))
        sm.add_widget(GroupSelectionScreen(name='group_selection'))
        sm.add_widget(ObserverReportSummaryScreen(name='observer_screen'))
        return sm

if __name__ == '__main__':
    MyApp().run()
