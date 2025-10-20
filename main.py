import argparse
import os
from datetime import datetime
import caldav
from icalendar import Calendar


def find_calendar_by_name(principal, calendar_name):
    """Find a calendar by its display name."""
    calendars = principal.calendars()
    for calendar in calendars:
        props = calendar.get_properties([caldav.dav.DisplayName()])
        display_name = props.get('{DAV:}displayname', '')
        if display_name == calendar_name:
            return calendar
    return None


def import_ics_to_icloud(username, password, ics_file_path, calendar_name="Alex Plugg"):
    """Import an ICS file to a specific iCloud calendar."""
    
    # iCloud CalDAV URL
    url = "https://caldav.icloud.com/"
    
    try:
        # Connect to iCloud CalDAV
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        
        # Find the target calendar
        target_calendar = find_calendar_by_name(principal, calendar_name)
        if not target_calendar:
            print(f"Calendar '{calendar_name}' not found. Available calendars:")
            calendars = principal.calendars()
            for calendar in calendars:
                props = calendar.get_properties([caldav.dav.DisplayName()])
                display_name = props.get('{DAV:}displayname', 'Unknown')
                print(f"  - {display_name}")
            return False
        
        # Read and parse the ICS file
        with open(ics_file_path, 'rb') as f:
            ics_content = f.read()
        
        calendar_data = Calendar.from_ical(ics_content)
        
        # Import each event from the ICS file
        events_imported = 0
        for component in calendar_data.walk():
            if component.name == "VEVENT":
                # Create a new calendar with just this event
                new_cal = Calendar()
                new_cal.add_component(component)
                
                # Add the event to the target calendar
                target_calendar.save_event(new_cal.to_ical().decode('utf-8'))
                events_imported += 1
                
                # Print event details
                summary = component.get('summary', 'No title')
                dtstart = component.get('dtstart')
                if dtstart:
                    start_time = dtstart.dt
                    print(f"Imported: {summary} ({start_time})")
                else:
                    print(f"Imported: {summary}")
        
        print(f"\nSuccessfully imported {events_imported} events to '{calendar_name}' calendar")
        return True
        
    except Exception as e:
        print(f"Error importing ICS file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Import ICS file to iCloud calendar')
    parser.add_argument('ics_file', help='Path to the ICS file to import')
    parser.add_argument('--username', '-u', help='iCloud username (email)')
    parser.add_argument('--password', '-p', help='iCloud app-specific password')
    parser.add_argument('--calendar', '-c', default='Alex Plugg', 
                       help='Calendar name to import to (default: Alex Plugg)')
    
    args = parser.parse_args()
    
    # Get credentials from environment variables if not provided
    username = args.username or os.getenv('ICLOUD_USERNAME')
    password = args.password or os.getenv('ICLOUD_PASSWORD')
    
    if not username:
        username = input("iCloud username (email): ")
    
    if not password:
        import getpass
        password = getpass.getpass("iCloud app-specific password: ")
    
    if not os.path.exists(args.ics_file):
        print(f"Error: ICS file '{args.ics_file}' not found")
        return 1
    
    success = import_ics_to_icloud(username, password, args.ics_file, args.calendar)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
