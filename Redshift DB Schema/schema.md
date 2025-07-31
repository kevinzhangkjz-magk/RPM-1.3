flowchart TB
  %%–– desri_analytics database ––%%
  subgraph desri_analytics["desri_analytics (database)"]

    %%–– analytics schema expanded ––%%
    subgraph analytics_schema["analytics (schema)"]

      backfill_tracker["**backfill_tracker**  
       • site (text)  
       • day (date)  
       • count (integer)  
       • run_date (date)"]

      cuyama_tee["**cuyama_tee**  
       • dateandtime_utc (timestamp)  
       • dateandtime (timestamp)  
       • tee_mw (float)  
       • tee_mwh (float)"]

      teee["**teee**  
       • dateandtime (timestamp)  
       • dateandtime_utc (timestamp)  
       • teee_mwh (float)  
       • teee_mw (float)"]

      exp_power_data["**exp_power_data**  
       • dateandtime (timestamp)  
       • site (text)  
       • p_exp (float)  
       • p_loss (float)"]

      inverter_setpoints["**inverter_setpoints**  
       • site (text)  
       • inverter_name (text)  
       • max_p (float)  
       • highest_by_site (float)  
       • relative_max (float)"]

      power_curves["**power_curves**  
       • site (text)  
       • air_density (float)  
       • windspeed (float)  
       • power_kw (float)  
       • comments (text)"]

      datashare_tables["**datashare_tables**  
       • schema (text)  
       • site (text)  
       • site_name (text)  
       • year (integer)  
       • month (integer)  
       • tablename (text)"]

      inverter_metadata["**inverter_metadata**  
       • site (text)  
       • device (text)  
       • nameplate_mw_ac (float)  
       • num_modules (integer)  
       • module_power_rating (float)  
       • comments (text)"]

      vw_datashare_tables["**vw_datashare_tables**  
       • schema (text)  
       • site (text)  
       • site_name (text)  
       • year (integer)  
       • month (integer)  
       • tablename (text)"]

      budget["**budget**  
       • site (text)  
       • year (integer)  
       • month (integer)  
       • gen_p50 (float)  
       • poa_p50 (float)  
       • ghi_p50 (float)  
       • comments (text)"]

      curtailment_data["**curtailment_data**  
       • site (text)  
       • tablename (text)  
       • curt_stat (float)  
       • writtenon (timestamp)  
       • curtailed (boolean)  
       • p_set (float)  
       • dateandtime (timestamp)"]

      problem_sensors["**problem_sensors**  
       • year (integer)  
       • month (integer)  
       • site (text)  
       • device_type (text)  
       • tagname (text)  
       • device (text)  
       • comments (text)"]

      derate_data["**derate_data**  
       • site (text)  
       • tablename (text)  
       • dt_day (date)  
       • inverter_name (text)  
       • hours_derated (float)  
       • writtenon (timestamp)  
       • poa_thresh (float)  
       • pct_nameplate_thresh (float)"]

      inverter_data["**inverter_data**  
       • site (text)  
       • dateandtime (timestamp)  
       • tablename (text)  
       • device (text)  
       • p_kw (float)  
       • poa (float)  
       • availability (float)  
       • datawrittenon (timestamp)"]

      inverter_data_rh3_2021["**inverter_data_rh3_2021**  
       • site (text)  
       • dateandtime (timestamp)  
       • tablename (text)  
       • device (text)  
       • p_kw (float)  
       • poa (float)  
       • availability (float)  
       • datawrittenon (timestamp)"]

      manual_curtailment_data["**manual_curtailment_data**  
       • site (text)  
       • day (date)  
       • generation_mwh (float)  
       • curtailment_mwh (float)  
       • total_billable_energy_mwh (float)  
       • site_name (text)  
       • column7 (text)  
       • column8 (text)"]

      old_problem_sensors["**old_problem_sensors**  
       • month (integer)  
       • year (integer)  
       • site (text)  
       • tablename (text)  
       • device_type (text)  
       • device (text)  
       • tagname (text)  
       • comments (text)"]

      site_daily_status_reports["**site_daily_status_reports**  
       • site (text)  
       • month (integer)  
       • day (integer)  
       • year (integer)  
       • comments (text)  
       • inverters_offline (integer)  
       • inverter_derates (integer)  
       • curtailment (integer)  
       • low_resource (integer)  
       • site_trip (integer)"]

      non_reporting_site_metadata["**non_reporting_site_metadata**  
       • site_name (text)  
       • inverter_manufacturer (text)  
       • inverter_count (integer)  
       • dc_capacity (float)  
       • ac_capacity_technical (float)  
       • ac_capacity_poi_limited (float)  
       • bifacial (boolean)  
       • asset_manager (text)  
       • state (text)  
       • utc_offset_std (text)  
       • utc_offset_dst (text)  
       • comments (text)  
       • site_id (integer)  
       • cod_date (date)"]

      flash_data["**flash_data**  
       • site (text)  
       • dateandtime (timestamp)  
       • tablename (text)  
       • p_mw (float)  
       • meter_counter_mwh (float)  
       • poa (float)  
       • ghi (float)  
       • bom_temp (float)  
       • air_temp (float)  
       • count_poa (integer)  
       • count_ghi (integer)  
       • count_bom (integer)  
       • count_airtemp (integer)  
       • datawrittenon (timestamp)"]

      site_metadata["**site_metadata**  
       • site (text)  
       • site_name (text)  
       • inverter_manufacturer (text)  
       • inverter_count (integer)  
       • dc_capacity (float)  
       • ac_capacity_technical (float)  
       • ac_capacity_poi_limited (float)  
       • bifacial (boolean)  
       • asset_manager (text)  
       • state (text)  
       • utc_offset_std (text)  
       • utc_offset_dst (text)  
       • comments (text)  
       • site_id (integer)  
       • cod_date (date)  
       • region (text)  
       • ppa_price (float)"]
    end

    %%–– other schemas in the database ––%%
    analytics_devops["analytics_devops"]
    analytics_devops_backup["analytics_devops_backup"]
    assembly2_deep_dive["assembly2_deep_dive"]
    assembly3_deep_dive["assembly3_deep_dive"]
    assembly_deep_dive["assembly_deep_dive"]
    catalog_history["catalog_history"]
    deep_dive_result_tables["deep_dive_result_tables"]
    device_meta_data["device_meta_data"]
    kawailoa_analysis["kawailoa_analysis"]
    pilot_projects["pilot_projects"]
    pilot_projects_copy["pilot_projects_copy"]
    poa_modelling["poa_modelling"]
    tracker_analytics["tracker_analytics"]

  end
