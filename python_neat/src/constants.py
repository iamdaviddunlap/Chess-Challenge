class Constants:
    # Low CPU mode flag
    half_power = True


    # General Parameters
    population_size = 100
    inputs_count = 284
    outputs_count = 1
    # inputs_count = 3
    # outputs_count = 1
    min_val = -99.999
    max_val = 99.999
    random_seed = 6969

    # Chess Parameters
    num_puzzles_per_game = 100

    # Parasites Settings
    num_hall_of_fame_parasites = 8
    num_champion_parasites = 4

    # HoF cleanup settings
    # max_hof_size = 75
    # min_reduced_hof_size = 25
    max_hof_size = 20
    min_reduced_hof_size = 10

    # Mutation Settings
    mutate_weights_prob = 0.6
    mutate_biases_prob = 0.6
    mutate_toggle_enable_prob = 0.1
    mutate_reenable_prob = 0.05
    mutate_remove_connection_prob = 0.05
    mutate_remove_node_prob = 0.01
    mutate_add_gate_prob = 0.1
    mutate_activation_function_prob = 0.1
    add_connection_prob = 0.3
    add_node_prob = 0.2

    # Perturbation Settings
    weight_perturb_chance = 0.6
    weight_perturb_value = 2.5
    bias_perturb_chance = 0.6
    bias_perturb_value = 2.5

    # Compatibility Settings
    disjoint_coeff = 2.0
    excess_coeff = 2.0
    gates_coeff = 1.0
    weight_coeff = 1.0
    species_compat_thresh_initial = 2.6
    species_compat_modifier = 0.3
    species_count_target = 10

    # Fitness Settings
    fitness_reward_win = 2.0
    fitness_reward_draw = -1.0
    fitness_reward_loss = 0.0
    fitness_penalty_factor_conn_count = 0.7
    fitness_penalty_factor_node_count = 0.3
    fitness_penalty_factor = 0.005

    # Breeding Settings
    superchamp_offspring = 5
    killer_superchamp_z_score_req = 5.0
    killer_superchamp_percent = 0.4
    mutate_only_prob = 0.25
    mate_only_prob = 0.2
    cross_species_mating_prob = 0.05
    cross_population_mating_prob = 0.001
    species_elite_percentage = 0.2
    inherit_disable_chance = 0.75

    # Mating Settings
    mate_avg_genes_prob = 0.4
