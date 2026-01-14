import marimo

__generated_with = "0.19.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import math
    return mo, pd


@app.cell
def _(mo):
    mo.md("""
    #HR Analytics
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(f"""
    # Load data
    """)
    return


@app.cell
def _(pd):
    general_data = pd.read_csv('/dev/hr_analytics/data/raw/general_data.csv')
    employee_survey_data = pd.read_csv('/dev/hr_analytics/data/raw/employee_survey_data.csv')
    manager_survey_data = pd.read_csv('/dev/hr_analytics/data/raw/manager_survey_data.csv')
    in_time = pd.read_csv('/dev/hr_analytics/data/raw/in_time.csv')
    out_time = pd.read_csv('/dev/hr_analytics/data/raw/out_time.csv')
    return (
        employee_survey_data,
        general_data,
        in_time,
        manager_survey_data,
        out_time,
    )


@app.cell
def _(general_data):
    print("===== General Data =====")
    general_data.info()
    general_data.head()
    return


@app.cell
def _(employee_survey_data):
    print('===== Employee Survey Data =====')
    employee_survey_data.info()
    employee_survey_data.head()
    return


@app.cell
def _(manager_survey_data):
    print('===== Manager Survey Data =====')
    manager_survey_data.info()
    manager_survey_data.head()
    return


@app.cell
def _(in_time):
    print("===== In Time =====")
    in_time.info()
    in_time.head()
    return


@app.cell
def _(out_time):
    print("===== Out Time =====")
    out_time.info()
    out_time.head()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Merge in_time and out_time

    Menggabungkan data `in_time` dan `out_time` untuk fitur kolom baru di master data.
    """)
    return


@app.cell
def _(in_time, out_time, pd):
    # Fix column
    in_dt = in_time.rename(columns={'Unnamed: 0': 'EmployeeID'}).copy()
    out_dt = out_time.rename(columns={'Unnamed: 0': 'EmployeeID'}).copy()

    # Calculate work hours per EmployeeID
    for col in in_dt.columns[1:]:
        in_dt[col] = pd.to_datetime(in_dt[col])
    for col in out_dt.columns[1:]:
        out_dt[col] = pd.to_datetime(out_dt[col])

    work_hours = (out_dt.iloc[:, 1:] - in_dt.iloc[:, 1:]).apply(
        lambda x: x.dt.total_seconds() / 3600
    )

    avg_work_hours = work_hours.mean(axis=1).round(2)

    work_hours = pd.concat(
        [in_dt['EmployeeID'], avg_work_hours.rename('AvgWorkHours')],
        axis=1
    ).copy()
    return in_dt, out_dt, work_hours


@app.cell
def _(employee_survey_data, general_data, manager_survey_data, work_hours):
    # Merge survey data into general data
    df = (
        general_data
        .merge(employee_survey_data, on='EmployeeID', how='left')
        .merge(manager_survey_data, on='EmployeeID', how='left')
        .merge(work_hours, on='EmployeeID', how='left')
    )
    return (df,)


@app.cell
def _(df, in_dt, out_dt, pd):
    # Count overtime frequency
    in_data = in_dt.set_index('EmployeeID')
    out_data = out_dt.set_index('EmployeeID')

    in_data = in_data.apply(pd.to_datetime)
    out_data = out_data.apply(pd.to_datetime)

    actual_hours = (out_data - in_data) / pd.Timedelta(hours=1)

    standard_hours_series = df.set_index('EmployeeID')['StandardHours']

    overtime_matrix = actual_hours.sub(standard_hours_series, axis=0)
    overtime_counts = (overtime_matrix > 0).sum(axis=1)
    overtime_counts.name = 'OvertimeFrequency'
    overtime_df = overtime_counts.reset_index()
    return (overtime_df,)


@app.cell
def _(df, overtime_df):
    df_merged = df.merge(overtime_df, on='EmployeeID', how='left')
    return (df_merged,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Handle missing values
    """)
    return


@app.cell
def _(df_merged):
    missing_columns = df_merged.columns[df_merged.isnull().any()].to_list()
    print(f"Kolom dengan missing values: {missing_columns}")
    print(df_merged[missing_columns].isnull().sum())
    return (missing_columns,)


@app.cell
def _(df_merged, missing_columns):
    # Handle on missing value columns
    for missing_col in missing_columns:
        df_merged[missing_col] = df_merged[missing_col].fillna(df_merged[missing_col].median())

    print("Status setelah imputasi (sisa missing values):")
    print(df_merged.isnull().sum().sum())
    return


@app.cell
def _(df_merged):
    # Check on duplicated data
    duplicates = df_merged.duplicated().sum()
    print(f"Jumlah data duplikat: {duplicates}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Handle outliers
    """)
    return


@app.cell
def _(df_merged):
    df_merged.info()
    return


@app.cell
def _(df_merged):
    outliers_columns = ['MonthlyIncome','DistanceFromHome','TotalWorkingYears','YearsAtCompany','YearsSinceLastPromotion','YearsWithCurrManager','AvgWorkHours']
    for _col in outliers_columns:
        if _col in df_merged.columns:
            q1, q3 = df_merged[_col].quantile(0.25), df_merged[_col].quantile(0.75),
            iqr = q3 - q1
            lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
            df_merged_outlier = df_merged[_col].clip(lower, upper)
    return (df_merged_outlier,)


@app.cell
def _(df_merged_outlier):
    df_merged_outlier.to_csv('/dev/hr_analytics/data/processed/hr_final.csv', index=False)
    print("Data berhasil disimpan ke ../data/interim/hr_analytics_clarified.csv")
    return


if __name__ == "__main__":
    app.run()
