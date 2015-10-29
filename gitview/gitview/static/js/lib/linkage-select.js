/**
 * @fileOverview This file has functions related to linkage-select element
 *		about projects and developers
 */


function removeDuplicate(sourceArray)
{
	var uniqueArray = new Array();
	sourceArray.sort(function(a, b){return a - b});
	var i = 0, j = 1;
	while(sourceArray[i] != undefined && sourceArray[j] != undefined)
	{
		if(sourceArray[i] != sourceArray[j])
		{
			uniqueArray.push(sourceArray[i]);
			i = j;
			j = i + 1;
		}
		else
		{
			j++;
		}
	}
	uniqueArray.push(sourceArray[i]);
	return uniqueArray;
}

function binarySearchArray(array, value)
{
	var i = 0, j = array.length;
	while (i < j)
	{
		var mid = Math.floor(i + (j - i) / 2);
		if (value < array[mid])
		{
			j = mid;
		}
		else if (value > array[mid])
		{
			i = mid + 1;
		}
		else
		{
			return true;
		}
	}
	return false;
}

function getSingleLevelItemsByIndex(indexArray, itemsArray)
{
	var result = _.filter(itemsArray, function(item){
		return binarySearchArray(indexArray, item.key);
	});
	return result;
}

function getDoubleLevelItemsByIndex(indexArray, itemsArray)
{
	var result = new Array();
	$.each(itemsArray, function(key, item){
		var subresult = _.filter(item.values, function(subitem){
			return binarySearchArray(indexArray, subitem.key);
		});
		if (!_.isEmpty(subresult))
		{
			result.push({
				'key': item.key,
				'text': item.text,
				'values': subresult
			});
		}
	});
	return result;
}

