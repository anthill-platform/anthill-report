CREATE TABLE `reports` (
  `report_id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `gamespace_id` int(11) unsigned NOT NULL,
  `account_id` int(11) unsigned NOT NULL,
  `application_name` varchar(64) NOT NULL DEFAULT '',
  `application_version` varchar(64) NOT NULL DEFAULT '',
  `report_category` varchar(64) NOT NULL DEFAULT '',
  `report_message` varchar(255) NOT NULL DEFAULT '',
  `report_info` json NOT NULL,
  `report_payload` mediumblob NOT NULL,
  `report_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `report_format` enum('BINARY','TEXT','JSON') NOT NULL DEFAULT 'BINARY',
  PRIMARY KEY (`report_id`),
  KEY `report_category` (`report_category`),
  KEY `account_id` (`account_id`),
  FULLTEXT KEY `report_message` (`report_message`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;