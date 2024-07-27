from bigquery.queryWrap import send_query
from decimal import Decimal
from datetime import datetime
import json
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Converts datetime to ISO 8601 string format
        return super(CustomEncoder, self).default(obj)

tableName = "bravo-six-428908.bitcoin_data.transactions"

def scrape_wallet(wallet_hash: str) -> str:
    query = f"""WITH `inp_addr` AS( SELECT `address`, `mtab`.`hash`, `inp`.`value` FROM `{tableName}` AS `mtab`, UNNEST(`mtab`.`inputs`) `inp`, UNNEST(`inp`.`addresses`) AS `address` WHERE `address` = "{wallet_hash}" ), `out_addr` AS( SELECT `address`, `mtab`.`hash`, `out`.`value` FROM `{tableName}` AS `mtab`, UNNEST(`mtab`.`outputs`) `out`, UNNEST(`out`.`addresses`) AS `address` WHERE `address` = "{wallet_hash}" ), `joined_table` AS ( SELECT `inp`.`value` AS `inp_val`, `out`.`value` AS `out_val` FROM `inp_addr` AS `inp` INNER JOIN `out_addr` AS `out` ON `inp`.`address` = `out`.`address` ), `unionized_table` AS ( SELECT `address`, ARRAY_AGG(DISTINCT `hash`) AS `tx` FROM ( SELECT `address`, `hash` FROM `inp_addr` UNION DISTINCT SELECT `address`, `hash` FROM `out_addr` ) GROUP BY `address` ), `aggr_data` AS ( SELECT SUM(`join`.`inp_val`) AS `total_received`, SUM(`join`.`out_val`) AS `total_sent`, SUM(`join`.`inp_val`) - SUM(`join`.`out_val`) AS `balance` FROM `joined_table` AS `join` ), `prep_mtab` AS ( SELECT `mtab`.`hash` AS `tx_hash`, `mtab`.`block_hash`, ARRAY_LENGTH(`mtab`.`inputs`) AS `tx_input_n`, ARRAY_LENGTH(`mtab`.`outputs`)AS `tx_output_n`, (SELECT sum(`value`) from UNNEST(`inputs`)) as `value`, `mtab`.`block_timestamp` AS `confirmed` FROM `{tableName}` AS `mtab`, UNNEST(`mtab`.`inputs`) AS `minp` ) SELECT `uni`.`address` AS `address`, `aggr`.*, ARRAY_LENGTH(`uni`.`tx`) AS `n_tx`, ARRAY(SELECT AS STRUCT * FROM UNNEST(`uni`.`tx`) `tx`, `prep_mtab` AS `mtab` WHERE `mtab`.`tx_hash` = `tx`) AS `txrefs` FROM `unionized_table` AS `uni`, `aggr_data` AS `aggr`;"""
    return json.loads(json.dumps(send_query(query), cls=CustomEncoder))


def scrape_transaction(tx_hash: str) -> str:
    query = f"""WITH `denested_inp` AS ( SELECT `ntab`.`hash` AS `tx_hash`, `inps`.`spent_transaction_hash` AS `prev_hash`, `inps`.`spent_output_index` AS `output_index`, FROM `{tableName}` AS `ntab`, UNNEST(`ntab`.`inputs`) AS `inps` ), `denested_out` AS ( SELECT `out`.`value`, `out`.`script_hex` AS `script`, `out`.`addresses`, `out`.`index`, `ntab`.`hash` AS `tx_hash` FROM `{tableName}` AS `ntab`, UNNEST(`ntab`.`outputs`) AS `out` ), `joined` AS ( SELECT `dot`.*, COALESCE(`dip`.`tx_hash`) AS `spent_by` FROM `denested_out` AS `dot` LEFT JOIN `denested_inp` AS `dip` ON `dot`.`tx_hash` = `dip`.`prev_hash` AND `dot`.`index` = `dip`.`output_index` ) SELECT `mtab`.`hash`, `mtab`.`block_hash`, `mtab`.`block_number` AS `block_height`, (SELECT sum(`value`) from UNNEST(`inputs`)) AS `total`, `mtab`.`fee` AS `fees`, `mtab`.`size`, `mtab`.`virtual_size` AS `vsize`, `mtab`.`block_timestamp` AS `received`, `mtab`.`version` AS `ver`, (SELECT count(*) FROM UNNEST(`inputs`)) AS `vin_sz`, (SELECT count(*) FROM UNNEST(`outputs`)) AS `vout_sz`, ARRAY( SELECT AS STRUCT `spent_transaction_hash` AS `prev_hash`, `spent_output_index` AS `output_index`, `value` AS `output_value`, `addresses`, `mtab`.`block_number` AS `age` FROM UNNEST(`inputs`) ) as `inputs`, ARRAY(SELECT AS STRUCT * FROM `joined` AS `joi` WHERE `joi`.`tx_hash` = `mtab`.`hash`) AS `outputs` FROM `{tableName}` AS `mtab` WHERE `hash` = "{tx_hash}";"""
    return json.loads(json.dumps(send_query(query), cls=CustomEncoder))
