from django.shortcuts import render, HttpResponse

from dashboard.models import *
from collections import Counter
from dashboard.forms import ModelParametersForm
from dashboard import optimization

from pulp import *

import pandas as pd
import numpy as np
from sklearn import linear_model 

import datetime

from openpyxl import *
import xlsxwriter
from io import BytesIO as IO


def home(request):
    return render(request, 'dashboard/home.html', {'title': 'Home'})

def statistics(request):
    context = {}
    
    #Customer Charts
    customers = Customers.objects.all()
    customer_names = [c.customer_name.city_name for c in customers]
    customer_demands = [d.demand for d in customers]
    #customer_regions = list(set([r.customer_name.region for r in customers]))

    customer_counter = Counter(r.customer_name.region for r in customers)
    customer_regions = []
    customer_regions_count = []
    for key, value in customer_counter.items():
        customer_regions.append(key)
        customer_regions_count.append(value)

    context['customer_names'] = customer_names
    context['customer_demands'] = customer_demands
    context['customer_regions'] = customer_regions
    context['customer_regions_count'] = customer_regions_count

    #Percentages for Pie Chart
    #print(sum(customer_regions_count))

    #Supplier Charts
    suppliers = Suppliers.objects.all()
    supplier_names = [s.supplier_name.city_name for s in suppliers]
    supplier_operating_costs = [o.operating_cost for o in suppliers]
    #supplier_capacities = [c.capacity for c in suppliers]

    supplier_counter = Counter(c.capacity for c in suppliers)
    supplier_capacities = []
    supplier_capacities_count = []
    for key, value in supplier_counter.items():
        supplier_capacities.append(key)
        supplier_capacities_count.append(value)
    
    context['supplier_names'] = supplier_names
    context['supplier_operating_costs'] = supplier_operating_costs
    context['supplier_capacities'] = supplier_capacities
    context['supplier_capacities_count'] = supplier_capacities_count
    

    return render(request, 'dashboard/statistics.html', context)

def demand_forecast(request):
    context = {}
    
    sales = Sales.objects.all()
    dates = [sale.sale_date for sale in sales] 
    sales_amounts = [sale.amount for sale in sales] 
    sales_customer_names = [sale.customer.customer_name.city_name for sale in sales] 

    sales = {'Date': dates, 'Sold Amount': sales_amounts, 'Customer': sales_customer_names}
    sales_data = pd.DataFrame(sales)
    sales_data['Date'] = pd.to_datetime(sales_data['Date'])
    #print(sales_data)

    customers = Customers.objects.all()
    customer_ids = [c.id for c in customers]
    customers_dict = {}
    for id in customer_ids:
        customer_sales = Sales.objects.all().filter(customer=id)
        dates = [cs.sale_date for cs in customer_sales] 
        amounts = [cs.amount for cs in customer_sales]
        customer_name = customer_sales[0].customer.customer_name.city_name
        customers_dict[customer_name] = {'Dates': dates, 'Amounts': amounts}

    customer_names = [c.customer_name.city_name for c in customers]
    context["customer_names"] = customer_names

    context['option'] = False
    context['customers'] = ['Istanbul', 'Ankara']
    context['predicted_demands'] = [5, 4]
    context['customer_name'] = 'Istanbul'
    context['customer_dict'] = customers_dict['Istanbul']

    if request.method == 'POST':
        #print(request.POST)
        if 'customer-chart' in request.POST:
            selected_customer = request.POST.get('select')
            print(selected_customer)
            context['customer_name'] = selected_customer
            context['customer_dict'] = customers_dict[selected_customer]

        if 'moving-average' in request.POST:
            def forecastDemand(df):
                #MOVING AVERAGE
                df = df.reset_index()
                #print(df)
                window_size = 6
                sum = 0
                for i in range(len(df) - window_size, len(df)):
                    sum += df.loc[i, 'Sold Amount']

                predicted_demand = int(sum/window_size)
                return predicted_demand

            predicted_demands = sales_data.groupby('Customer').apply(forecastDemand)
            customers = predicted_demands.index.tolist()
            predicted_demands = list(predicted_demands)
            context['customers'] = customers
            context['predicted_demands'] = predicted_demands
            context['option'] = True

        elif 'linear-regression' in request.POST:
            def forecastDemand(df):
                #LINEAR REGRESSION  
                df = df.set_index('Date')
                df['Month'] = (df.index).month
                #print(df)

                x = df['Month'].values.reshape(-1, 1)
                y = df['Sold Amount'].values

                model = linear_model.LinearRegression().fit(x, y)
                linear_model.LinearRegression(copy_X=True, fit_intercept=True, n_jobs=1, normalize=False)
                predicted_demand = int(model.predict([[13]])[0])
                return predicted_demand

            predicted_demands = sales_data.groupby('Customer').apply(forecastDemand)
            customers = predicted_demands.index.tolist()
            predicted_demands = list(predicted_demands)
            context['customers'] = customers
            context['predicted_demands'] = predicted_demands
            context['option'] = True
        
    
    return render(request, 'dashboard/demand-forecast.html', context)

def cost_calculation(request):
    return render (request, 'dashboard/cost-calculation.html', {'title': 'Cost Calculation'})

def capacity_planning(request):
    context = {}

    customers = Customers.objects.all()
    suppliers = Suppliers.objects.all()

    #SETS
    supplier_names = [s.supplier_name.city_name for s in suppliers] #V1
    customer_names = [c.customer_name.city_name for c in customers] #V2

    #PARAMETERS
    supplier_capacities = [c.capacity for c in suppliers]
    customer_demands = [d.demand for d in customers]
    supplier_operating_costs = [o.operating_cost for o in suppliers]

    supplier = {'Supplier': supplier_names, 'Capacity': supplier_capacities, 'Operating Cost': supplier_operating_costs}
    supplier_data = pd.DataFrame(supplier)
    customer = {'Customer': customer_names, 'Demand': customer_demands}
    customer_data = pd.DataFrame(customer)

    context["supplier_data"] = supplier_data.to_html(index=False)
    context["customer_data"] = customer_data.to_html(index=False)
    context["supplier_names"] = supplier_names
    context["customer_names"] = customer_names
    context["len_suppliers"] = len(supplier_names)

    if request.method == 'POST':
        parametersDict = dict(request.POST.lists())
        if 'solve' in parametersDict:
            #print(request.POST)
            parametersDict = dict(request.POST.lists())
            del parametersDict['csrfmiddlewaretoken']
            del parametersDict['number-supplier']
            del parametersDict['number-customer']
            del parametersDict['solve']
            #print(parametersDict)

            number_supplier = request.POST.get('number-supplier') #''
            number_customer = request.POST.get('number-customer') #''
            if number_supplier != '':
                number_supplier = int(number_supplier)
            if number_customer != '':
                number_customer = int(number_customer)/100
            #print(number_supplier)
            #print(number_customer)

            suppliers_should_opened = []
            unsatisfied_demand_costs = {}
            for key, value in parametersDict.items(): 
                if value[0] == 'on':
                    suppliers_should_opened.append(key)
                    if len(value) != 1 and value[1] != '':
                        unsatisfied_demand_costs[key] = float(value[1])
                if value[0] != 'on' and value[0] != '':
                    unsatisfied_demand_costs[key] = float(value[0])       
            #print(suppliers_should_opened)
            #print(unsatisfied_demand_costs)

            #PARAMETERS VALIDATION
            parameters_not_valid = False
            error_messages = []
            if len(unsatisfied_demand_costs) > 0 and (len(unsatisfied_demand_costs) != len(customer_names)):
                error_messages.append('Please enter all unit costs of unsatisfied demand of customers!')
                parameters_not_valid = True
            if len(unsatisfied_demand_costs) > 0 and number_customer == '':
                error_messages.append('Please fill in both customer optional areas!')
                parameters_not_valid = True

            if parameters_not_valid:
                context['error_messages'] = error_messages
                return render(request, 'dashboard/capacity-planning.html', context)
            else:
                context['output'] = True
                results = optimization.solveModel(supplier_names, customer_names, supplier_capacities, customer_demands, supplier_operating_costs, 
                                                        number_supplier, number_customer, suppliers_should_opened, unsatisfied_demand_costs)

                #Output Map Values
                shipping_amount_values = results['shippingAmountValues_dict']
                opened_suppliers = results['openedSuppliers']
                cities_list = list(set(opened_suppliers + customer_names))
                map_dict = {'City': [], 'Coords': [], 'Used Capacity': [], 'Satisfied Demand': [], 'Type': []}
                for city in cities_list:
                    map_dict['City'].append(city)
                    c = Citys.objects.get(city_name=city)
                    latitude = c.latitude
                    longitude = c.longitude
                    map_dict['Coords'].append({'lat': latitude, 'lng': longitude})
                    used_capacity = 0
                    satisfied_demand = 0
                    if (city in customer_names) and (city in opened_suppliers):
                        map_dict['Type'].append('b')
                        for j in customer_names:
                            used_capacity += shipping_amount_values[city][j]
                        map_dict['Used Capacity'].append(used_capacity)
                        for i in opened_suppliers:
                            satisfied_demand += shipping_amount_values[i][city]
                        map_dict['Satisfied Demand'].append(satisfied_demand)
                    elif city in customer_names:
                        map_dict['Type'].append('c')
                        for i in opened_suppliers:
                            satisfied_demand += shipping_amount_values[i][city]
                        map_dict['Satisfied Demand'].append(satisfied_demand)
                        map_dict['Used Capacity'].append('-')
                    elif city in opened_suppliers:
                        map_dict['Type'].append('s')
                        for j in customer_names:
                            used_capacity += shipping_amount_values[city][j]
                        map_dict['Used Capacity'].append(used_capacity)
                        map_dict['Satisfied Demand'].append('-')

                context['map_dict'] = map_dict
                        
                #Objective Values
                context['modelStatus'] = results['modelStatus']
                context['objectiveValue'] = results['objectiveValue']

                #Decision Variables Values 
                supplierValues = results['supplierValues'].to_html(index=False)
                context['supplierValues'] = supplierValues
                shippingAmountValues = results['shippingAmountValues'].to_html(index=True)
                context['shippingAmountValues'] = shippingAmountValues
                #optional
                customerValues = results['customerValues']
                if len(customerValues) > 0:
                    customerValues = customerValues.to_html(index=False)
                    context['option'] = True
                else:   
                    context['option'] = False
                context['customerValues'] = customerValues 

                global shipping_amounts_data
                shipping_amounts_data  = results['shippingAmountValues']
                global suppliers_data
                suppliers_data = results['supplierValues']
                global customers_data
                customers_data = results['customerValues']

        elif 'export' in parametersDict:
                excel_file = IO()

                with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:  
                    shipping_amounts_data.to_excel(writer, sheet_name='Shipping Amounts')
                    suppliers_data.to_excel(writer, sheet_name='Suppliers')
                    if len(customers_data) > 0:
                        customers_data.to_excel(writer, sheet_name='Customers')

                writer.save()
                writer.close()

                excel_file.seek(0)

                response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment;filename=Results.xlsx'       
                return response
                
            
        
            



        '''
        context["test_sorted_html"] = test_data_sorted.to_html(index=False, classes="table table-bordered table-condensed table-responsive-md table-striped text-center")
        '''
        '''
        if request.method == 'POST':
            form = ModelParametersForm(request.POST)
            if form.is_valid():
                print("VALID")
        else:
            form = ModelParametersForm()
        
        context['form'] = form
        '''


    return render(request, 'dashboard/capacity-planning.html', context)

def update_data(request):
    return render(request, 'dashboard/update-data.html', {'title': 'Update Data'})