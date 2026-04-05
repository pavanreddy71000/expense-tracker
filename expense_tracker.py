"""
Expense Tracker - Personal finance tracking desktop application.

Tracks income and expense transactions, manages budgets, computes
financial summaries, and visualizes spending by category.

Built with Python, tkinter, Pandas, and Matplotlib.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ExpenseTracker:
    """Main application class handling UI, data processing, and persistence."""

    def __init__(self, master):
        self.master = master
        self.master.title("Expense Tracker")
        self.master.geometry('1000x800')

        self.canvas = tk.Canvas(master, borderwidth=0)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.vsb = ttk.Scrollbar(master, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.file_name = 'expenses_data.pkl'
        self.load_initial_data()

        self.create_widgets()
        self.load_data()
        self.update_financials()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_initial_data(self):
        """Load saved data from disk, or initialize empty state if no file exists."""
        if os.path.isfile(self.file_name):
            data = pd.read_pickle(self.file_name)
            if isinstance(data, dict):
                self.df = pd.DataFrame(data.get('expenses', []))
                self.budget = data.get('budget', 0)
            else:
                self.df = pd.DataFrame(
                    columns=['Transaction Date', 'Transaction Description',
                             'Transaction Category', 'Transaction Amount']
                )
                self.budget = 0
        else:
            self.df = pd.DataFrame(
                columns=['Transaction Date', 'Transaction Description',
                         'Transaction Category', 'Transaction Amount']
            )
            self.budget = 0

    def create_widgets(self):
        """Build the full UI: form inputs, transaction table, stats bar, and chart button."""
        ttk.Label(
            self.scrollable_frame, text="Expense Tracker",
            font=("Helvetica", 16)
        ).grid(row=0, column=0, columnspan=4, pady=10)

        form_frame = ttk.Frame(self.scrollable_frame)
        form_frame.grid(row=1, column=0, columnspan=4, padx=20, pady=10, sticky='ew')

        ttk.Label(form_frame, text="Transaction Date (YYYY-MM-DD):").grid(row=0, column=0, sticky='e')
        self.date_entry = ttk.Entry(form_frame)
        self.date_entry.grid(row=0, column=1, sticky='ew')

        ttk.Label(form_frame, text="Transaction Description:").grid(row=0, column=2, sticky='e')
        self.description_entry = ttk.Entry(form_frame)
        self.description_entry.grid(row=0, column=3, sticky='ew')

        ttk.Label(form_frame, text="Transaction Category:").grid(row=1, column=0, sticky='e')
        self.category_combobox = ttk.Combobox(
            form_frame,
            values=['Utilities', 'Groceries', 'Food', 'Miscellaneous', 'Transportation', 'Income']
        )
        self.category_combobox.grid(row=1, column=1, sticky='ew')
        self.category_combobox.set('Select or Type')

        ttk.Label(form_frame, text="Transaction Amount:").grid(row=1, column=2, sticky='e')
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.grid(row=1, column=3, sticky='ew')

        ttk.Label(form_frame, text="Set Budget:").grid(row=2, column=0, sticky='e')
        self.budget_entry = ttk.Entry(form_frame)
        self.budget_entry.grid(row=2, column=1, sticky='ew')
        ttk.Button(form_frame, text="Set Budget", command=self.set_budget).grid(row=2, column=2)

        ttk.Button(form_frame, text="Add Transaction", command=self.add_transaction).grid(row=3, column=1)
        ttk.Button(form_frame, text="Delete Selected Transaction", command=self.delete_transaction).grid(row=3, column=2)
        ttk.Button(form_frame, text="Reset All Transactions", command=self.reset_transactions).grid(row=3, column=3)

        self.tree = ttk.Treeview(
            self.scrollable_frame,
            columns=('Transaction Date', 'Transaction Description',
                     'Transaction Category', 'Transaction Amount'),
            show='headings'
        )
        self.tree.grid(row=4, column=0, columnspan=4, padx=20, pady=10, sticky='ew')
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor='center')

        stats_frame = ttk.Frame(self.scrollable_frame)
        stats_frame.grid(row=5, column=0, columnspan=4, padx=20, pady=5, sticky='ew')
        self.total_income_label = ttk.Label(stats_frame, text="Total Income: $0", font=("Helvetica", 12))
        self.total_income_label.pack(side='left')
        self.budget_label = ttk.Label(stats_frame, text="Budget: $0", font=("Helvetica", 12))
        self.budget_label.pack(side='left')
        self.budget_remaining_label = ttk.Label(stats_frame, text="Budget Remaining: $0", font=("Helvetica", 12))
        self.budget_remaining_label.pack(side='left')
        self.total_savings_label = ttk.Label(stats_frame, text="Total Savings: $0", font=("Helvetica", 12))
        self.total_savings_label.pack(side='right')

        ttk.Button(
            self.scrollable_frame, text="Show Charts", command=self.show_charts
        ).grid(row=6, column=0, columnspan=4, pady=20)

    def show_charts(self):
        """Generate a pie chart of expenses grouped by category."""
        if not self.df.empty:
            expense_df = self.df[self.df['Transaction Category'] != 'Income']
            expense_df['Transaction Amount'] = pd.to_numeric(
                expense_df['Transaction Amount'], errors='coerce'
            )
            summary = expense_df.groupby('Transaction Category')['Transaction Amount'].sum()
            if summary.empty:
                messagebox.showinfo("No Data", "No expense data to plot.")
                return
            fig, ax = plt.subplots()
            ax.pie(summary, labels=summary.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            plt.show()

    def set_budget(self):
        """Validate and set the monthly budget from user input."""
        try:
            self.budget = float(self.budget_entry.get())
            self.update_financials()
            messagebox.showinfo("Budget Set", f"Budget has been set to ${self.budget:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the budget.")

    def add_transaction(self):
        """Validate all input fields and add a new transaction to the DataFrame."""
        if (not self.date_entry.get() or not self.description_entry.get()
                or not self.category_combobox.get() or not self.amount_entry.get()):
            messagebox.showerror(
                "Missing Information",
                "Please complete all fields to add a transaction."
            )
            return
        try:
            transaction_date = datetime.datetime.strptime(self.date_entry.get(), '%Y-%m-%d')
            amount = float(self.amount_entry.get())
            new_row = {
                'Transaction Date': transaction_date,
                'Transaction Description': self.description_entry.get(),
                'Transaction Category': self.category_combobox.get(),
                'Transaction Amount': amount
            }
            self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
            self.update_financials()
            self.load_data()
            self.clear_entries()
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))

    def delete_transaction(self):
        """Remove the selected transaction from the DataFrame and refresh the table."""
        selected_items = self.tree.selection()
        if selected_items:
            for item in selected_items:
                item_values = self.tree.item(item, "values")
                item_index = self.df[
                    (self.df['Transaction Date'] == item_values[0]) &
                    (self.df['Transaction Description'] == item_values[1]) &
                    (self.df['Transaction Category'] == item_values[2]) &
                    (self.df['Transaction Amount'] == float(item_values[3]))
                ].index
                self.df.drop(item_index, inplace=True)
                self.tree.delete(item)
            self.update_financials()
            self.load_data()
        else:
            messagebox.showinfo("Selection Needed", "Please select a transaction to delete.")

    def reset_transactions(self):
        """Clear all transactions and reset the table to empty state."""
        self.df = pd.DataFrame(
            columns=['Transaction Date', 'Transaction Description',
                     'Transaction Category', 'Transaction Amount']
        )
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_financials()

    def load_data(self):
        """Refresh the treeview table with current DataFrame contents, sorted by date."""
        self.tree.delete(*self.tree.get_children())
        if not self.df.empty:
            self.df['Transaction Date'] = pd.to_datetime(self.df['Transaction Date'])
            sorted_df = self.df.sort_values('Transaction Date')
            for idx, row in sorted_df.iterrows():
                self.tree.insert('', 'end', values=[
                    row['Transaction Date'].strftime('%Y-%m-%d'),
                    row['Transaction Description'],
                    row['Transaction Category'],
                    row['Transaction Amount']
                ])

    def clear_entries(self):
        """Clear all input fields after a successful transaction add."""
        self.date_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.category_combobox.set('')
        self.amount_entry.delete(0, tk.END)
        self.budget_entry.delete(0, tk.END)

    def update_financials(self):
        """Recalculate and display income, expenses, savings, and budget status."""
        if self.df.empty:
            self.total_income_label.config(text="Total Income: $0.00")
            self.budget_label.config(text=f"Budget: ${self.budget:.2f}")
            self.budget_remaining_label.config(text=f"Budget Remaining: ${self.budget:.2f}")
            self.total_savings_label.config(text="Total Savings: $0.00")
        else:
            total_income = self.df[
                self.df['Transaction Category'] == 'Income'
            ]['Transaction Amount'].astype(float).sum()
            total_expenses = self.df[
                self.df['Transaction Category'] != 'Income'
            ]['Transaction Amount'].astype(float).sum()
            total_savings = total_income - total_expenses
            remaining_budget = self.budget - total_expenses
            self.total_income_label.config(text=f"Total Income: ${total_income:.2f}")
            self.budget_label.config(text=f"Budget: ${self.budget:.2f}")
            self.budget_remaining_label.config(text=f"Budget Remaining: ${remaining_budget:.2f}")
            self.total_savings_label.config(text=f"Total Savings: ${total_savings:.2f}")
            if 0 < remaining_budget <= 100:
                messagebox.showwarning(
                    "Budget Alert",
                    f"You are close to your budget limit! Only ${remaining_budget:.2f} left."
                )

    def on_closing(self):
        """Serialize application state to disk before exit."""
        data = {
            'expenses': self.df.to_dict('records'),
            'budget': self.budget
        }
        pd.to_pickle(data, self.file_name)
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
