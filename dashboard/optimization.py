    
from pulp import *
from dashboard.models import *
import pandas as pd

def solveModel(supplier_names, customer_names, supplier_capacities, customer_demands, supplier_operating_costs, number_supplier, number_customer, suppliers_should_opened, unsatisfied_demand_costs):

    customers = Customers.objects.all()
    suppliers = Suppliers.objects.all()
    results = {}

    #OPTIMIZATION MODEL
    model = LpProblem("Capacity Planning Problem", LpMinimize)
    
    #PARAMETERS
    #Dictionary of capacity of suppliers
    capacities_dict = {} 
    for i in range(len(supplier_names)):
        capacities_dict[supplier_names[i]] = supplier_capacities[i] #qi

    #Dictionary of demand of customers
    demands_dict = {} 
    for j in range(len(customer_names)):
        demands_dict[customer_names[j]] = customer_demands[j] #dj

    #Dictionary of operating cost of suppliers
    operating_costs_dict = {}
    for i in range(len(supplier_names)):
        operating_costs_dict[supplier_names[i]] = supplier_operating_costs[i] #fi

    #Dictionary of unit cost of suppliers to customers
    supplier_ids= [s.id for s in suppliers] 
    customer_ids = [c.id for c in customers] 
    
    unit_costs_dict = {}
    for i in supplier_ids:
        customers_dict = {}
        for j in customer_ids:
            shipping = Shipping.objects.get(supplier=i, customer=j)  
            customers_dict[shipping.customer.customer_name.city_name] = shipping.unit_cost

        unit_costs_dict[shipping.supplier.supplier_name.city_name] = customers_dict #cij

    #Dictionary of unit cost of unsatisfied demand for customers
    if len(unsatisfied_demand_costs) > 0:
        unsatisfied_demand_costs_dict = {}
        for j in customer_names:
            unsatisfied_demand_costs_dict[j] = unsatisfied_demand_costs[j] #pj

    routes = [(i,j) for i in supplier_names for j in customer_names]

    #DECISION VARIABLES
    shipping_amounts = LpVariable.dicts("ShippingAmount", (supplier_names, customer_names), 0, None, LpInteger) #sij
    supplier_is_opened = LpVariable.dicts("SupplierIsOpened", supplier_names, 0, 1, LpBinary) #yi
    unsatisfied_amounts = LpVariable.dicts("UnsatisfiedAmount", customer_names, 0, None, LpInteger) #zj
    customer_is_satisfied = LpVariable.dicts("CustomerIsSatisfied", customer_names, 0, 1, LpBinary) #wj
    #print(supplier_is_opened['Istanbul'])

    #OBJECTIVE FUNCTION
    if len(unsatisfied_demand_costs) > 0:
        objective_function = (lpSum(unit_costs_dict[i][j]*shipping_amounts[i][j] for (i, j) in routes) + 
                            lpSum(operating_costs_dict[i]*supplier_is_opened[i] for i in supplier_names) +
                            lpSum(unsatisfied_demand_costs_dict[j]*unsatisfied_amounts[j] for j in customer_names))
    else:
        objective_function = (lpSum(unit_costs_dict[i][j]*shipping_amounts[i][j] for (i, j) in routes) + 
                            lpSum(operating_costs_dict[i]*supplier_is_opened[i] for i in supplier_names))
    model += objective_function

    #CONSTRAINTS
    #Capacity Constraint
    for i in supplier_names:
        model += lpSum(shipping_amounts[i][j] for j in customer_names) <= capacities_dict[i]*supplier_is_opened[i]

    #Demand Constraint
    if len(unsatisfied_demand_costs) > 0:
        for j in customer_names:
            model += (lpSum(shipping_amounts[i][j] for i in supplier_names) + unsatisfied_amounts[j]) == demands_dict[j]
    else:
        for j in customer_names:
            model += lpSum(shipping_amounts[i][j] for i in supplier_names) == demands_dict[j]

    #Supplier Optional Constraints
    if len(suppliers_should_opened) > 0:
        for i in suppliers_should_opened:
            model += supplier_is_opened[i] == 1
    if number_supplier != '':
        model += lpSum(supplier_is_opened[i] for i in supplier_names) == number_supplier

    #Customer Optional Constraints
    if len(unsatisfied_demand_costs) > 0:
        for j in customer_names:
            model += unsatisfied_amounts[j] <= (demands_dict[j]*(1 - customer_is_satisfied[j]))
        
        model += lpSum(customer_is_satisfied[j] for j in customer_names) >= (number_customer*len(customer_names))

    model.solve()

    #modelStatus, objectiveValue, yi, wj, zj, sij
    
    print("Status: ", LpStatus[model.status])

    for v in model.variables():
        if v.varValue > 0:
            print(v.name, "=", v.varValue)

    print("Total cost = ", value(model.objective))  

    #varValue ile decision variable'ların değerlerinin dictionary'si yapılacak!
    #print(supplier_is_opened['Istanbul'].varValue)
    #print(shipping_amounts['Istanbul']['Istanbul'].varValue)

    results['modelStatus'] = LpStatus[model.status]
    results['objectiveValue'] = round(value(model.objective), 2)

    supplier_is_opened_values = []
    opened_suppliers = []
    not_opened_suppliers = []
    for variable in supplier_is_opened:
        if supplier_is_opened[variable].varValue > 0:
            supplier_is_opened_values.append('Yes')
            opened_suppliers.append(variable)
        else:
            supplier_is_opened_values.append('No')
            not_opened_suppliers.append(variable)
    
    results['openedSuppliers'] = opened_suppliers
    results['notOpenedSuppliers'] = not_opened_suppliers

    supplierValues = {'Supplier': supplier_names, 'Is Opened': supplier_is_opened_values}
    supplierValues = pd.DataFrame(supplierValues)

    results['supplierValues'] = supplierValues

    shipping_amounts_values = {}
    for i in supplier_names:
        if supplier_is_opened[i].varValue > 0:
            customer_values = {}
            for j in customer_names:
                customer_values[j] = int(shipping_amounts[i][j].varValue)

            shipping_amounts_values[i] = customer_values

    results['shippingAmountValues_dict'] = shipping_amounts_values
    shippingAmountValues = pd.DataFrame(shipping_amounts_values)
    shippingAmountValues = shippingAmountValues.transpose()
    results['shippingAmountValues'] = shippingAmountValues

    #optional
    if len(unsatisfied_demand_costs) > 0:
        customer_is_satisfied_values = []
        unsatisfied_amounts_values = []
        for variable in customer_is_satisfied:
            if customer_is_satisfied[variable].varValue > 0:
                customer_is_satisfied_values.append('Yes')
            else:
                customer_is_satisfied_values.append('No')
            unsatisfied_amounts_values.append(int(unsatisfied_amounts[variable].varValue))

        customerValues = {'Customer': customer_names, 'Is Satisfied': customer_is_satisfied_values, 'Unsatisfied Demand Amount': unsatisfied_amounts_values}
        customerValues = pd.DataFrame(customerValues)

        results['customerValues'] = customerValues
    else:
        results['customerValues'] = pd.DataFrame()
    

    return results