from delta_targets import generate_delta
from datetime import datetime

DATE_FORMAT = "%d/%m/%Y"

if __name__ == "__main__":
    dataset = input("What dataset would you like deltas for: ")
    previous = input("Enter the start date for the delta (dd/mm/yyyy): ")
    current = input("Enter the end date for the delta (dd/mm/yyyy): ")
    cur = datetime.strptime(current, DATE_FORMAT)
    prev = datetime.strptime(previous, DATE_FORMAT)
    generate_delta(dataset, cur, prev)
