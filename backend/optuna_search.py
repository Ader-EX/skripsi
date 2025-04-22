# import optuna
# from sqlalchemy.orm import Session
# from database import get_db 
# from routes.hybrid_routes import hybrid_schedule  

# penalties = {
#     "room_conflict": 2,
#     "lecturer_conflict": 2,
#     "cross_day": 1,
#     "invalid_timeslot": 2,
#     "wrong_room": 2,
#     "special_needs": 2,
#     "daily_load": 1,
#     "high_priority_preference": 2,
#     "general_preference": 1,
#     "jabatan": 2,
#     "conflict_multiplier": 100,
# }

# db: Session = next(get_db())

# def objective(trial: optuna.Trial) -> float:
#     population_size      = trial.suggest_int   ("population_size",      20, 200)
#     generations          = trial.suggest_int   ("generations",          10, 100)
#     mutation_prob        = trial.suggest_float ("mutation_prob",        0.01, 0.5)
#     initial_temperature  = trial.suggest_float ("initial_temperature",  100.0, 10000.0, log=True)
#     cooling_rate         = trial.suggest_float ("cooling_rate",         0.80, 0.99)
#     iterations_per_temp  = trial.suggest_int   ("iterations_per_temp",  10, 500)

#     #  Call function
#     result = hybrid_schedule(
#         db=db,
#         population_size=population_size,
#         generations=generations,
#         mutation_prob=mutation_prob,
#         initial_temperature=initial_temperature,
#         cooling_rate=cooling_rate,
#         iterations_per_temp=iterations_per_temp,
#         penalties=penalties,
#     )

    
#     return result["final_fitness"]

# if __name__ == "__main__":
    
#     study = optuna.create_study(
#         direction="minimize",
#         sampler=optuna.samplers.TPESampler(),
#         pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
#     )

#     study.optimize(objective, n_trials=10, timeout=3600)

#     print("Best parameters: ", study.best_params)
#     print("Best (lowest) fitness: ", study.best_value)
