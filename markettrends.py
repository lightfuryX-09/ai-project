#market trends analysis
import tkinter as tk 
from tkinter import messagebox 
import pandas as pd 
import matplotlib.pyplot as plt
import wikipedia 

def get_crop_info():
    crop = crop_entry.get().strip()
    if not crop:
        messagebox.showwarning(
            "Input Required"
            "Please enter a crop name"
        )
        return
    try:
        results = wikipedia.search(crop)
        if not results:
            messagebox.showinfo(
                "No Result"
                f"No Wikipedia page found for '{crop}'."    
            )
            return 
        page_title = results[0]
        summary = wikipedia.summary( 
            page_title,
            sentences=5,
            auto_suggest=False 
        )
           
        info_box.delete("1.0", tk.END)
        info_box.insert(
            tk.END,
            f"CROP INFORMATION\n"
            f"Crop: {page_title}\n\n"
            f"{summary}"
        )

    except wikipedia.exceptions.DisambiguationError as e:
        info_box.delete("1.0", tk.END)
        info_box.insert(
            tk.END,
            "Multiple pages found.\n\n"
            "Try one of these:\n\n"
            + "\n".join(e.options[:10])
        )   
    except Exception as e:
        messagebox.showerror(
            "Wikipedia Error",
            str(e)
        )

def analyze_price():
    crop = crop_entry.get().strip()
    location = location_entry.get().strip()
    if not location:
        messagebox.showwarning(
            "Input Required",
            "Please enter a location"
        )        
        return
    try:
        df = pd.read_csv("crop_price.csv")
        crop_df = df[
            (df["Crop"].str.lower() == crop.lower()) &
            (df["Location"].str.lower() == location.lower())
        ]

        if len(crop_df) == 0:
            messagebox.showinfo(
                "No Data",
                f"No price data found for {crop} in {location}."
            )
            return
        
        crop_df["Date"] = pd.to_datetime(crop_df["Date"])
        crop_df = crop_df.sort_values("Date")
        avg_price = crop_df["Price"].mean()
        max_price = crop_df["Price"].max()
        min_price = crop_df["Price"].min()
        latest_price = crop_df.iloc[-1]["Price"]
        result = f"""
PRICE ANALYSIS
==========================================================
Crop: {crop}

Location: {location}

Average Price: {avg_price:.2f}

Maximum Price: {max_price:.2f}

Minimum price: {min_price:.2f}

Latest Price: {latest_price:.2f}
"""
        
        info_box.delete("1.0", tk.END)
        info_box.insert(tk.END, result)

        #Trend Graph

        plt.figure(figsize=(8, 5))

        plt.plot(
            crop_df["Date"],
            crop_df["Price"],
            marker="o"
        )

        plt.xlabel("Date")
        plt.ylabel("Price ")
        plt.grid(True)

        plt.tight_layout()
        
        plt.show()

    except FileNotFoundError:

        messagebox.showerror(
            "File error",
            "crop_price.csv not found."
        )

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )
        
#---------------------------------
# GUI
#------------------------------------

root = tk.Tk()
root.title("Crop Price Trend Analyzer")
root.geometry("900x650")

title = tk.Label(
    root,
    text="Crop Price Trend Analyzer",
    font=("Arial", 18, "bold")
)
title.pack(pady=10)

# Crop Name 
crop_label = tk.Label(
    root,
    text="Enter Crop Name:"
)
crop_label.pack()
crop_entry = tk.Entry(
    root,
    width=40
)
crop_entry.pack(pady=5)

#location 
location_label = tk.Label(
    root,
    text="Enter Location:"
)
location_label.pack()

location_entry = tk.Entry(
    root,
    width=40
)
location_entry.pack(pady=5)

#Buttons
wiki_btn = tk.Button(
    root,
    text="Get Crop Information",
    command=get_crop_info
)
wiki_btn.pack(pady=5)

trend_btn= tk.Button(
    root, 
    text="Analyze Price Trend",
    command=analyze_price
)
trend_btn.pack(pady=5)

#Output Box 
info_box= tk.Text(
    root,
    height=20,
    width=100
)
info_box.pack(pady=10)

root.mainloop()



