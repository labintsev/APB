import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. Моделирование спроса и предложения
Q_max = 20      # Максимальный объём рекламного времени за сутки, %
N = 20        # Количество точек для моделирования
q = np.linspace(0, Q_max, N)

# Параметры линейной модели предложения
P_min = 0.9                         # Минимальная цена (руб.) при нулевом объёме предложения
k_s = 0.01                          # Коэффициент роста (подбирается для реалистичного наклона)
P_supply = P_min + k_s * q 

# Параметры модели спроса
P_max = 2                           # максимальная цена при нулевом объёме спроса
k_d = - 0.1                         # коэффициент затухания
velocity_d = 1.5                      # Скорость роста цены при увеличении объёма предложения
P_demand = P_max + velocity_d * (np.exp(k_d * q) - 1)


# 2. Моделирование выручки без участия в ассоциации

t = 3600 * 15 * q / 100                     # Проданное время за сутки, секунд (активное время - 15 часов)
people = 100                                # Охват аудитории, тысяч человек 
cost = 1e-6 * t**2 + 0.1 * t + 80           # переменные и фиксированные затраты       
revenue = people * t * np.min(np.stack([P_supply, P_demand]), axis=0) / 600 
profit = revenue - cost

# 3. Моделирование выручки с участием в ассоциации
t_apb = np.linspace(2, 20, N) * 3600 * 15 / 100
revenue_apb  = people * t_apb * np.min(np.stack([P_supply, P_demand]), axis=0) / 600  + 2
profit_apb = revenue_apb - cost

df = pd.DataFrame({
    'q, %': q,
    'P_supply, руб.': [int(p) for p in P_supply],
    'P_demand, руб.': [int(p) for p in P_demand],
    't, сек.': [int(t_) for t_ in t],
    'revenue, тыс. руб.': [int(r) for r in revenue],
    'cost, тыс. руб.': [int(c) for c in cost],
    'profit, тыс. руб.': [int(p) for p in profit],
    't_apb, сек.': [int(t_apb_) for t_apb_ in t_apb],
    'profit_apb, тыс. руб.': [int(p) for p in profit_apb]
})
df.to_csv('simulate/supply-demand.csv', index=False)

# 4. Визуализация результатов

# Построение графиков спроса и предложения
plt.figure(figsize=(10, 6))
plt.xlabel('Доля рекламы в эфире, q [%]')
plt.ylabel('Цена 1 секунды рекламы на аудиторию 1000 человек (руб.)')

plt.plot(q, P_supply, label=f'Предложение', color='darkorange')
plt.plot(q, P_demand, label=f'Спрос', color='blue')

plt.title('Кривые предложения и спроса', fontsize=16, fontweight='bold', pad=20)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11, loc='upper right')

plt.xlim(0, Q_max)
plt.ylim(0, P_max)
plt.tight_layout()
plt.savefig('simulate/supply-demand.png')


# Построение графиков выручки и затрат
plt.figure(figsize=(10, 6))
plt.xlabel('Проданное время за сутки, [сек.]')
plt.ylabel('Выручка и затраты, [тыс. руб.]') 

plt.plot(t, revenue, label='Выручка', color='darkorange')
plt.plot(t, cost, label='Затраты', color='blue')
plt.plot(t, profit, label='Прибыль', color='green')
plt.plot(t_apb, profit_apb, label='Прибыль c ассоциацией', color='red', linestyle='dashed')

plt.title('Выручка и затраты', fontsize=16, fontweight='bold', pad=20)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=11, loc='upper left')
plt.ylim(0, max(revenue))
plt.xlim(0, 10_000)
plt.tight_layout()

plt.savefig('simulate/revenue-cost-profitablity.png')