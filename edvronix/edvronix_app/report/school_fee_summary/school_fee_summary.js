frappe.query_reports["School Fee Summary"] = {

    "filters": [

        {
            "fieldname": "academic_year",
            "label": "Academic Year",
            "fieldtype": "Link",
            "options": "Academic Year"
        },

        {
            "fieldname": "program",
            "label": "Program",
            "fieldtype": "Link",
            "options": "Program"
        },

        {
            "fieldname": "month",
            "label": "Month",
            "fieldtype": "Select",
            "options": [
                "",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ]
        }

    ]

};