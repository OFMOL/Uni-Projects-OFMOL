import numpy as np
from scipy.optimize import linprog
from datetime import datetime, timedelta




class Material:
    # Обьявление материала
    def __init__(self, label, quantity):
        self.label = label
        self.quantity = quantity







class Coffee(Material):



    def __init__(self, label, quantity, country, region, state="green", profit_per_kg=0, green_coffee_cost=0, pack_025_cost=0, pack_05_cost=0):
        super().__init__(label, quantity)
        self.country = country
        self.region = region
        self.state = state  # 'green' or 'roasted'
        self.profit_per_kg = profit_per_kg  # прибыль за кг обжаренного кофе
        self.green_coffee_cost = green_coffee_cost  # стоимость 1 кг зеленого зерна
        self.pack_025_cost = pack_025_cost  # стоимость 0.25 кг упаковки
        self.pack_05_cost = pack_05_cost  # стоимость 0.5 кг упаковки




    def roast(self, quantity):
        if self.state == "green":
            if quantity > self.quantity:
                raise ValueError("Not enough green coffee to roast.")
            self.quantity -= quantity
            roasted_quantity = quantity * 0.75  # Уменьшение веса на 25%
            roasted_coffee = Coffee(
                self.label, roasted_quantity, self.country, self.region, state="roasted",
                profit_per_kg=self.profit_per_kg,
                green_coffee_cost=self.green_coffee_cost,
                pack_025_cost=self.pack_025_cost,
                pack_05_cost=self.pack_05_cost
            )
            print(f"Roasted {quantity} kg of {self.label} from {self.country}, {self.region}. New roasted quantity: {roasted_quantity} kg")
            return roasted_coffee
        else:
            raise ValueError("Coffee is already roasted.")







class Sklad:

    # Создаем склад
    def __init__(self, capacity, label):
        self.capacity = capacity
        self.label = label
        self.materials = {}
        self.production_plan = {}  # Initialize production_plan attribute



    # добавление материалов (в том числе кофе) на склад
    def add_material(self, material, quantity):
        if quantity < 0:
            raise ValueError("Quantity must be positive.")

        if self.get_total_quantity() + quantity > self.capacity:
            raise ValueError("Not enough capacity in the sklad.")

        key = (material.label, material.state) if isinstance(material, Coffee) else (material.label, None)
        if key in self.materials:
            self.materials[key].quantity += quantity
        else:
            self.materials[key] = material
            self.materials[key].quantity = quantity  # устанавливаем количество
        print(f"Added {quantity} of {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) to {self.label}.")




    # вычитание материалов (в том числе кофе) со склада
    def remove_material(self, material, quantity):
        key = (material.label, material.state) if isinstance(material, Coffee) else (material.label, None)
        if key not in self.materials:
            raise ValueError(f"No material with label {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) found in {self.label}.")

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        if quantity > self.materials[key].quantity:
            raise ValueError(f"Not enough material {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) to remove.")

        self.materials[key].quantity -= quantity

        if self.materials[key].quantity == 0:
            del self.materials[key]
        print(f"Removed {quantity} of {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) from {self.label}.")



    # Перемещение материалов
    def transfer_material(self, target_sklad, material, quantity=None):
        key = (material.label, material.state) if isinstance(material, Coffee) else (material.label, None)
        if key not in self.materials:
            raise ValueError(f"No material with label {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) found in {self.label}.")

        if quantity is None:
            quantity = self.materials[key].quantity

        self.remove_material(material, quantity)
        target_sklad.add_material(material, quantity)
        print(f"Transferred {quantity} of {material.label} ({material.state if isinstance(material, Coffee) else 'N/A'}) from {self.label} to {target_sklad.label}.")




    # Добавление обжаренного кофе как отдельного материала на склад
    def roast_coffee(self, coffee_label, quantity):
        key = (coffee_label, "green")
        if key not in self.materials:
            raise ValueError(f"No coffee with label {coffee_label} found in {self.label}.")
        coffee = self.materials[key]
        roasted_coffee = coffee.roast(quantity)
        self.add_material(roasted_coffee, roasted_coffee.quantity)



    # Общее количество кофе на складе
    def get_total_quantity(self):
        return sum(material.quantity for material in self.materials.values())



    # Функция для линейного программирования
    def optimize_production(self, profits, constraints, b):
        # Separate transportation time constraints
        transport_constraints = []
        transport_b = []

        transport_time = 20  # minutes
        num_products = len(profits)

        for i in range(num_products):
            row = [0] * num_products
            row[i] = transport_time
            transport_constraints.append(row)
            transport_b.append(0)

        # Convert constraints and b to numpy arrays
        constraints_np = np.array(constraints, dtype=float)
        transport_constraints_np = np.array(transport_constraints, dtype=float)
        b_np = np.array(b, dtype=float)
        transport_b_np = np.array(transport_b, dtype=float)

        # Combine constraints
        combined_constraints = np.vstack((constraints_np, transport_constraints_np))
        combined_b = np.hstack((b_np, transport_b_np))

        # profits - список прибыли за единицу каждого вида продукции

        # Преобразуем прибыли в отрицательные, т.к. linprog минимизирует целевую функцию
        c = [-profit for profit in profits]

        # Решаем задачу линейного программирования
        result = linprog(c, A_ub=combined_constraints, b_ub=combined_b, method='highs')

        if result.success:
            print("Optimization successful!")
            print(f"Optimal production quantities: {result.x}")
            return result.x
        else:
            print("Optimization failed.")
            return None
        



    def set_production_requirements(self, coffee_label, roasted_coffee_needed, packs_025_needed, packs_05_needed):
        # First, obtain the current production plan
        production_plan = self.plan()

        # Check if the coffee_label exists in the current production plan
        if coffee_label not in production_plan:
            raise ValueError(f"Coffee label '{coffee_label}' not found in current production plan.")

        # Update production requirements for the specified coffee
        production_plan[coffee_label]["roasted_coffee"] = roasted_coffee_needed
        production_plan[coffee_label]["pack_025"] = packs_025_needed
        production_plan[coffee_label]["pack_05"] = packs_05_needed

        # Calculate additional roasted coffee needed for packing
        packs_025_additional = packs_025_needed - production_plan[coffee_label]["pack_025"]
        packs_05_additional = packs_05_needed - production_plan[coffee_label]["pack_05"]

        # Convert pack quantities to roasted coffee quantity
        roasted_coffee_for_packs = packs_025_additional * 0.25 + packs_05_additional * 0.5

        # Update roasted coffee requirement to include packing needs
        production_plan[coffee_label]["roasted_coffee"] += roasted_coffee_for_packs

        # Set the updated production plan to the class attribute
        self.production_plan = production_plan

        print(f"Updated production requirements for {coffee_label} on {self.label}.")





    # вывод строки объясняющей что это за склад
    def __str__(self):
        return f'Sklad "{self.label}" с вместимостью {self.capacity} единиц.'

    # Обновление вместимости склада
    def update_capacity(self, new_capacity):
        self.capacity = new_capacity
        print(f'Вместимость склада "{self.label}" обновлена до {self.capacity} единиц.')

    # Обновление названия склада
    def update_label(self, new_label):
        self.label = new_label
        print(f'Метка склада обновлена на "{self.label}".')

    # "очистка" склада (обнуление в том числе наименования)
    def clear(self):
        self.capacity = 0
        self.label = ''
        self.materials.clear()
        print('Склад был очищен.')

    # Функция для просмотра материалов на складе
    def view_materials(self):
        for (label, state), material in self.materials.items():
            print(f"{label}: {material.quantity} ({state if state else 'N/A'})")





    def plan(self):
        # Create a daily production plan
        print(f"=== Production Plan for {datetime.now().date()} ===")
        print(f"Sklad: {self.label}")

        # Calculate available time for roasting
        working_hours = 10  # total working hours in a shift
        roasting_time_per_batch = 20  # minutes
        roasting_capacity = 50  # maximum quantity of green coffee to roast per batch
        roasting_time = timedelta(minutes=roasting_time_per_batch)
        roasting_batches = working_hours * 60 // roasting_time_per_batch

        # Track production requirements
        production_plan = {
            "Brazil Serado": {
                "roasted_coffee": 0,
                "pack_025": 0,
                "pack_05": 0
            },
            "Ethiopia Acacia": {
                "roasted_coffee": 0,
                "pack_025": 0,
                "pack_05": 0
            },
            "Indonesia Frinsa": {
                "roasted_coffee": 0,
                "pack_025": 0,
                "pack_05": 0
            }
        }

        # Update with specific production requirements if set
        for coffee_label, requirements in self.production_plan.items():
            production_plan[coffee_label]["roasted_coffee"] = requirements.get("roasted_coffee", 0)
            production_plan[coffee_label]["pack_025"] = requirements.get("pack_025", 0)
            production_plan[coffee_label]["pack_05"] = requirements.get("pack_05", 0)

        # Plan roasting
        for (label, state), material in self.materials.items():
            if isinstance(material, Coffee) and material.state == "green":
                roasting_batches_possible = min(roasting_batches, material.quantity // roasting_capacity)
                if roasting_batches_possible > 0:
                    roasting_quantity = roasting_batches_possible * roasting_capacity
                    roasted_coffee = self.roast_coffee(material.label, roasting_quantity)
                    print(f"Roasting {roasted_coffee.quantity} kg of {material.label}.")
                    production_plan[material.label]["roasted_coffee"] += roasted_coffee.quantity

        # Check if enough green coffee for roasting
        for coffee_label, requirements in production_plan.items():
            roasted_needed = requirements["roasted_coffee"]
            current_green = self.materials.get((coffee_label, "green"), Material(coffee_label, 0)).quantity
            if roasted_needed > current_green:
                to_roast = roasted_needed - current_green
                try:
                    roasted_coffee = self.roast_coffee(coffee_label, to_roast)
                    print(f"Roasting additional {roasted_coffee.quantity} kg of {coffee_label} to meet production needs.")
                    production_plan[coffee_label]["roasted_coffee"] += roasted_coffee.quantity
                except ValueError as e:
                    print(f"Error: {e}")
                    # Handle the situation where roasting additional coffee fails
                    # This could include ordering more green coffee or adjusting production plans

        # Plan transferring roasted coffee
        for (label, state), material in list(self.materials.items()):  # Convert to list to iterate safely
            if isinstance(material, Coffee) and material.state == "roasted":
                self.transfer_material(general_sklad, material)
                if label in production_plan:
                    production_plan[label]["roasted_coffee"] += material.quantity

        # Plan packing roasted coffee
        for coffee_label, requirements in production_plan.items():
            roasted_quantity = requirements["roasted_coffee"]
            packs_025 = requirements["pack_025"]
            packs_05 = requirements["pack_05"]

            if packs_025 > 0:
                print(f"Need to produce {packs_025} packs of 0.25 kg for {coffee_label}.")
                production_plan[coffee_label]["pack_025"] = packs_025

            if packs_05 > 0:
                print(f"Need to produce {packs_05} packs of 0.5 kg for {coffee_label}.")
                production_plan[coffee_label]["pack_05"] = packs_05

        print("Production planning completed.")

        # Return the production plan for further use if needed
        return production_plan




# Цены закупки
green_coffee_prices = {
    "Brazil Serado": 300,
    "Ethiopia Acacia": 400,
    "Indonesia Frinsa": 430
}

pack_prices = {
    "0.25": {
        "Brazil Serado": 467,
        "Ethiopia Acacia": 529,
        "Indonesia Frinsa": 493
    },
    "0.5": {
        "Brazil Serado": 935,
        "Ethiopia Acacia": 930,
        "Indonesia Frinsa": 990
    }
}


# Создаем склады
general_sklad = Sklad(200000, "General Sklad")
factory_sklad = Sklad(300000, "Factory Sklad")


# Создаем материалы
pack_0_25 = Material("Pack 0,25", 100)
pack_0_5 = Material("Pack 0,5", 50)


# Create coffees
Brazil_Serado = Coffee("Brazil Serado", 700, "Brazil", "Serado", profit_per_kg=1000, green_coffee_cost=green_coffee_prices["Brazil Serado"], pack_025_cost=pack_prices["0.25"]["Brazil Serado"], pack_05_cost=pack_prices["0.5"]["Brazil Serado"])
Ethiopia_Acacia = Coffee("Ethiopia Acacia", 300, "Ethiopia", "Acacia", profit_per_kg=1200, green_coffee_cost=green_coffee_prices["Ethiopia Acacia"], pack_025_cost=pack_prices["0.25"]["Ethiopia Acacia"], pack_05_cost=pack_prices["0.5"]["Ethiopia Acacia"])
Indonesia_Frinsa = Coffee("Indonesia Frinsa", 200, "Indonesia", "Frinsa", profit_per_kg=1500, green_coffee_cost=green_coffee_prices["Indonesia Frinsa"], pack_025_cost=pack_prices["0.25"]["Indonesia Frinsa"], pack_05_cost=pack_prices["0.5"]["Indonesia Frinsa"])



# Добавляем кофе на склады
general_sklad.add_material(Brazil_Serado, 510)
factory_sklad.add_material(Brazil_Serado, 50)
factory_sklad.add_material(Ethiopia_Acacia, 30)
general_sklad.add_material(Indonesia_Frinsa, 200)
factory_sklad.add_material(Indonesia_Frinsa, 0) 


# Добавляем материалы на склады
general_sklad.add_material(pack_0_25, 700)
factory_sklad.add_material(pack_0_5, 500)



# Обжариваем партию кофе на производственном складе (2 раза по 15 кг)
factory_sklad.roast_coffee("Brazil Serado", 15)
factory_sklad.roast_coffee("Brazil Serado", 15)

# Обжариваем партию кофе на производственном складе (1 раз 30 кг)
factory_sklad.roast_coffee("Ethiopia Acacia", 30)





#ОПТИМИЗАЦИЯ 
# Optimization setup
profits = [Brazil_Serado.profit_per_kg, Ethiopia_Acacia.profit_per_kg, Indonesia_Frinsa.profit_per_kg]
num_products = len(profits)

# Constraints and b vector setup
constraints = []
b = []

# Example of how to set label_index based on label, you might need to adjust based on your actual Coffee class implementation
coffee_types = [Brazil_Serado, Ethiopia_Acacia, Indonesia_Frinsa]
for i, coffee in enumerate(coffee_types):
    label_index = i  # Assuming index corresponds to label
    # Constraint for green coffee
    constraint_green = [0] * num_products
    constraint_green[label_index] = 1
    constraints.append(constraint_green)
    b.append(factory_sklad.materials[(coffee.label, "green")].quantity)

    # Constraint for roasted coffee (considering roasted coffee on all warehouses)
    constraint_roasted = [0] * num_products
    constraint_roasted[label_index] = -1
    for sklad in [general_sklad, factory_sklad]:
        if (coffee.label, "roasted") in sklad.materials:
            constraint_roasted[label_index] += 1
    constraints.append(constraint_roasted)
    b.append(0)  # Since we want to minimize, we don't want more roasted coffee than needed

# Optimize production
optimal_quantities = factory_sklad.optimize_production(profits, constraints, b)

# Transfer roasted coffee to general_sklad and pack them
if optimal_quantities is not None:
    for i, coffee in enumerate(coffee_types):
        quantity = optimal_quantities[i]
        if quantity > 0:
            factory_sklad.transfer_material(general_sklad, coffee, quantity)
            # Distribute roasted coffee into packs
            packs_025 = quantity // 0.25
            packs_05 = (quantity % 0.25) // 0.5
            if packs_025 > 0:
                general_sklad.add_material(Material(f"{coffee.label} 0.25kg pack", packs_025), packs_025 * coffee.pack_025_cost)
            if packs_05 > 0:
                general_sklad.add_material(Material(f"{coffee.label} 0.5kg pack", packs_05), packs_05 * coffee.pack_05_cost)

            # Check if improved plan is feasible and handle it
            if packs_025 + packs_05 < 100:
                # Calculate the quantity if we had up to 100 packs
                improved_quantity = (packs_025 + packs_05) * 0.25 + (quantity % 0.25)
                if improved_quantity > quantity:
                    improved_quantity = quantity
                improved_packs_025 = improved_quantity // 0.25
                improved_packs_05 = (improved_quantity % 0.25) // 0.5
                if improved_packs_025 > packs_025:
                    general_sklad.add_material(Material(f"{coffee.label} 0.25kg pack", improved_packs_025 - packs_025), (improved_packs_025 - packs_025) * coffee.pack_025_cost)
                if improved_packs_05 > packs_05:
                    general_sklad.add_material(Material(f"{coffee.label} 0.5kg pack", improved_packs_05 - packs_05), (improved_packs_05 - packs_05) * coffee.pack_05_cost)




# Устанавливаем новые требования к производству для кофе 
#factory_sklad.set_production_requirements("Brazil Serado", 100, 50, 30)
#factory_sklad.set_production_requirements("Ethiopia Acacia", 0, 20, 46)
#factory_sklad.set_production_requirements("Indonesia Frinsa", 0, 38, 10)

# Планирование производства с учетом новых требований
production_plan = factory_sklad.plan()

# Update production plan with consideration for green coffee used in roasting and packing
for coffee_label, requirements in production_plan.items():
    roasted_coffee_needed = requirements['roasted_coffee']
    pack_025_needed = requirements['pack_025'] * 0.25
    pack_05_needed = requirements['pack_05'] * 0.5

    # Calculate total green coffee required (including for roasting and packing)
    total_green_coffee = roasted_coffee_needed + pack_025_needed + pack_05_needed

    # Update the production plan with total green coffee required
    production_plan[coffee_label]['green_coffee_needed'] = total_green_coffee

# Print updated production plan with green coffee consumption included
print("\n=== Updated Production Plan Summary ===")
for coffee_label, requirements in production_plan.items():
    print(f"{coffee_label}:")
    print(f"- Green coffee needed: {requirements['green_coffee_needed']} kg")
    print(f"- Roasted coffee needed: {requirements['roasted_coffee']} kg")
    print(f"- Packs of 0.25 kg: {requirements['pack_025']}")
    print(f"- Packs of 0.5 kg: {requirements['pack_05']}")
    print()