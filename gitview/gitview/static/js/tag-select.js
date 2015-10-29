function addOptions(selectItem, optionIdList, optionDataList)
{
	var filterResult = getSingleLevelItemsByIndex(optionIdList, optionDataList);
	_.each(filterResult, function(optionItem){
		selectItem.append(new Option(optionItem['text'], optionItem['key']));
	});
}
